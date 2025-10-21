#!/bin/bash

# Service Health Check Script
# Monitors the health of all Sergas Super Account Manager services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configurations
BACKEND_URL="http://localhost:8008"
FRONTEND_URL="http://localhost:7008"
COPILOTKIT_URL="${FRONTEND_URL}/api/copilotkit"

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local service_name=$2
    local expected_status=${3:-200}

    echo -n "Checking ${service_name}... "

    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" -eq "$expected_status" ]; then
            echo -e "${GREEN}✅ OK${NC} (HTTP $response)"
            return 0
        else
            echo -e "${YELLOW}⚠️  HTTP $response${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

# Function to check backend health specifically
check_backend_health() {
    echo -n "Checking Backend Health... "

    if response=$(curl -s "$BACKEND_URL/health" 2>/dev/null); then
        if echo "$response" | grep -q '"status":"healthy"'; then
            echo -e "${GREEN}✅ Healthy${NC}"
            echo "   Service: $(echo "$response" | grep -o '"service":"[^"]*"' | cut -d'"' -f4)"
            echo "   Protocol: $(echo "$response" | grep -o '"protocol":"[^"]*"' | cut -d'"' -f4)"
            echo "   CopilotKit: $(echo "$response" | grep -o '"copilotkit_configured":[^,]*' | cut -d':' -f2)"
            agents=$(echo "$response" | grep -o '"agents_registered":[0-9]*' | cut -d':' -f2)
            echo "   Agents: $agents"
            return 0
        else
            echo -e "${RED}❌ Unhealthy response${NC}"
            echo "   Response: $response"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed to connect${NC}"
        return 1
    fi
}

# Function to check process ports
check_ports() {
    echo -e "${BLUE}📡 Port Usage:${NC}"

    if lsof -i :8008 >/dev/null 2>&1; then
        echo -e "   Port 8008 (Backend): ${GREEN}✅ In use${NC}"
        lsof -i :8008 | grep LISTEN | awk '{print "   Process: " $1 " (PID: " $2 ")"}'
    else
        echo -e "   Port 8008 (Backend): ${RED}❌ Not in use${NC}"
    fi

    if lsof -i :7007 >/dev/null 2>&1; then
        echo -e "   Port 7007 (Frontend): ${GREEN}✅ In use${NC}"
        lsof -i :7007 | grep LISTEN | awk '{print "   Process: " $1 " (PID: " $2 ")"}'
    else
        echo -e "   Port 7007 (Frontend): ${RED}❌ Not in use${NC}"
    fi
    echo
}

# Function to test CopilotKit integration
test_copilotkit() {
    echo -e "${BLUE}🤖 CopilotKit Integration Test:${NC}"

    # Test CopilotKit endpoint
    echo -n "Testing CopilotKit endpoint... "
    if response=$(curl -s "$COPILOTKIT_URL" 2>/dev/null); then
        if echo "$response" | grep -q '"status":"OK"'; then
            echo -e "${GREEN}✅ OK${NC}"
            echo "   Message: $(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
        else
            echo -e "${YELLOW}⚠️  Unexpected response${NC}"
            echo "   Response: $response"
        fi
    else
        echo -e "${RED}❌ Failed${NC}"
    fi

    # Test backend CopilotKit endpoint
    echo -n "Testing Backend CopilotKit API... "
    if response=$(curl -s -X POST "$BACKEND_URL/api/copilotkit" \
        -H "Content-Type: application/json" \
        -d '{"text":"test","actions":[]}' 2>/dev/null); then
        if echo "$response" | grep -q '"data"'; then
            echo -e "${GREEN}✅ OK${NC}"
            echo "   Integration working"
        else
            echo -e "${YELLOW}⚠️  API responded but may have issues${NC}"
            echo "   Response: $(echo "$response" | head -c 100)..."
        fi
    else
        echo -e "${RED}❌ Failed${NC}"
    fi
    echo
}

# Function to show service URLs
show_service_urls() {
    echo -e "${BLUE}🌐 Service URLs:${NC}"
    echo "   Backend API: $BACKEND_URL"
    echo "   API Docs: $BACKEND_URL/docs"
    echo "   OpenAPI Spec: $BACKEND_URL/openapi.json"
    echo "   Frontend: $FRONTEND_URL"
    echo "   CopilotKit API: $COPILOTKIT_URL"
    echo
}

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}🔍 Dependencies Check:${NC}"

    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        echo -e "   Python: ${GREEN}✅ $(python3 --version)${NC}"
    else
        echo -e "   Python: ${RED}❌ Not found${NC}"
    fi

    # Check Node.js
    if command -v node >/dev/null 2>&1; then
        echo -e "   Node.js: ${GREEN}✅ $(node --version)${NC}"
    else
        echo -e "   Node.js: ${RED}❌ Not found${NC}"
    fi

    # Check npm
    if command -v npm >/dev/null 2>&1; then
        echo -e "   npm: ${GREEN}✅ $(npm --version)${NC}"
    else
        echo -e "   npm: ${RED}❌ Not found${NC}"
    fi

    # Check uvicorn (for backend)
    if command -v uvicorn >/dev/null 2>&1; then
        echo -e "   Uvicorn: ${GREEN}✅ Installed${NC}"
    else
        echo -e "   Uvicorn: ${YELLOW}⚠️  Not in PATH (may be in venv)${NC}"
    fi
    echo
}

# Main health check function
main_health_check() {
    echo -e "${BLUE}🏥 Sergas Super Account Manager - Service Health Check${NC}"
    echo "=================================================="
    echo

    # Check dependencies
    check_dependencies

    # Check port usage
    check_ports

    # Check services
    echo -e "${BLUE}📊 Service Health:${NC}"

    backend_healthy=false
    frontend_healthy=false

    if check_backend_health; then
        backend_healthy=true
    fi

    if check_endpoint "$FRONTEND_URL" "Frontend"; then
        frontend_healthy=true
    fi

    check_endpoint "$BACKEND_URL/docs" "Backend Docs"
    echo

    # Test CopilotKit integration if both services are running
    if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
        test_copilotkit
    else
        echo -e "${YELLOW}⚠️  Skipping CopilotKit integration test (services not fully healthy)${NC}"
        echo
    fi

    # Show service URLs
    show_service_urls

    # Summary
    echo -e "${BLUE}📋 Summary:${NC}"
    if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
        echo -e "${GREEN}🎉 All services are running correctly!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Some services are not running properly${NC}"
        echo -e "${BLUE}💡 To start all services: ./scripts/service-health-check.sh start${NC}"
        exit 1
    fi
}

# Start services function
start_services() {
    echo -e "${BLUE}🚀 Starting Sergas Super Account Manager Services${NC}"
    echo "=================================================="

    # Check if backend is already running
    if curl -s "$BACKEND_URL/health" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Backend is already running${NC}"
    else
        echo -e "${BLUE}Starting backend...${NC}"
        cd "$(dirname "$0")/.."
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        uvicorn src.main:app --host 0.0.0.0 --port 8008 --reload &
        BACKEND_PID=$!
        echo "Backend started with PID: $BACKEND_PID"
        echo $BACKEND_PID > .backend.pid

        # Wait for backend to be healthy
        echo "Waiting for backend to be healthy..."
        for i in {1..30}; do
            if curl -s "$BACKEND_URL/health" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Backend is healthy${NC}"
                break
            fi
            sleep 1
        done
    fi

    # Check if frontend is already running
    if curl -s "$FRONTEND_URL" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Frontend is already running${NC}"
    else
        echo -e "${BLUE}Starting frontend...${NC}"
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        echo "Frontend started with PID: $FRONTEND_PID"
        echo $FRONTEND_PID > ../.frontend.pid

        # Wait for frontend to be ready
        echo "Waiting for frontend to be ready..."
        for i in {1..60}; do
            if curl -s "$FRONTEND_URL" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Frontend is ready${NC}"
                break
            fi
            sleep 1
        done
    fi

    echo
    echo -e "${GREEN}🎉 Services started successfully!${NC}"
    show_service_urls
}

# Stop services function
stop_services() {
    echo -e "${BLUE}🛑 Stopping Sergas Super Account Manager Services${NC}"
    echo "=================================================="

    # Stop backend
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo "Stopping backend (PID: $BACKEND_PID)..."
            kill "$BACKEND_PID"
            rm .backend.pid
        else
            echo "Backend process not found, removing PID file"
            rm .backend.pid
        fi
    else
        echo "No backend PID file found"
    fi

    # Stop frontend
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo "Stopping frontend (PID: $FRONTEND_PID)..."
            kill "$FRONTEND_PID"
            rm .frontend.pid
        else
            echo "Frontend process not found, removing PID file"
            rm .frontend.pid
        fi
    else
        echo "No frontend PID file found"
    fi

    # Force kill if processes are still running
    echo "Checking for remaining processes..."
    if lsof -i :8008 >/dev/null 2>&1; then
        echo "Force killing backend processes..."
        lsof -ti :8008 | xargs kill -9 2>/dev/null || true
    fi

    if lsof -i :7007 >/dev/null 2>&1; then
        echo "Force killing frontend processes..."
        lsof -ti :7007 | xargs kill -9 2>/dev/null || true
    fi

    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Parse command line arguments
case "${1:-check}" in
    check|status)
        main_health_check
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    *)
        echo "Usage: $0 {check|start|stop|restart|status}"
        echo "  check/status - Check health of all services"
        echo "  start       - Start all services"
        echo "  stop        - Stop all services"
        echo "  restart     - Restart all services"
        exit 1
        ;;
esac