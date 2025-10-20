#!/bin/bash
# Sergas Super Account Manager - Monitoring Stack Startup Script
# Generated: 2025-10-19

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_ROOT/docker/monitoring"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Sergas Monitoring Stack Startup${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}\n"

# Check if monitoring directory exists
if [ ! -d "$MONITORING_DIR" ]; then
    echo -e "${RED}Error: Monitoring directory not found at $MONITORING_DIR${NC}"
    exit 1
fi

# Change to monitoring directory
cd "$MONITORING_DIR"

# Stop existing containers
echo -e "${YELLOW}Stopping existing monitoring services...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ Existing services stopped${NC}\n"

# Pull latest images
echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker-compose pull
echo -e "${GREEN}✓ Images updated${NC}\n"

# Create necessary directories
echo -e "${YELLOW}Creating data directories...${NC}"
mkdir -p "$PROJECT_ROOT/data/prometheus"
mkdir -p "$PROJECT_ROOT/data/grafana"
mkdir -p "$PROJECT_ROOT/data/alertmanager"
echo -e "${GREEN}✓ Directories created${NC}\n"

# Set permissions
echo -e "${YELLOW}Setting directory permissions...${NC}"
chmod -R 777 "$PROJECT_ROOT/data" 2>/dev/null || true
echo -e "${GREEN}✓ Permissions set${NC}\n"

# Start services
echo -e "${YELLOW}Starting monitoring services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
echo -e "\n${YELLOW}Checking service health...${NC}\n"

check_service() {
    local name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name is healthy${NC}"
            return 0
        fi
        echo -ne "${YELLOW}  Waiting for $name... (attempt $attempt/$max_attempts)\r${NC}"
        sleep 2
        ((attempt++))
    done

    echo -e "${RED}✗ $name failed to start${NC}"
    return 1
}

# Check each service
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3000/api/health"
check_service "AlertManager" "http://localhost:9093/-/healthy"
check_service "Node Exporter" "http://localhost:9100/metrics"

# Display status
echo -e "\n${BLUE}=================================${NC}"
echo -e "${BLUE}Service Status${NC}"
echo -e "${BLUE}=================================${NC}\n"

docker-compose ps

# Display access information
echo -e "\n${BLUE}=================================${NC}"
echo -e "${BLUE}Access Information${NC}"
echo -e "${BLUE}=================================${NC}\n"

echo -e "${GREEN}Grafana Dashboard:${NC}"
echo -e "  URL: http://localhost:3000"
echo -e "  Username: admin"
echo -e "  Password: sergas_admin_2025\n"

echo -e "${GREEN}Prometheus:${NC}"
echo -e "  URL: http://localhost:9090\n"

echo -e "${GREEN}AlertManager:${NC}"
echo -e "  URL: http://localhost:9093\n"

echo -e "${GREEN}Node Exporter:${NC}"
echo -e "  Metrics: http://localhost:9100/metrics\n"

# Display dashboards
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Available Dashboards${NC}"
echo -e "${BLUE}=================================${NC}\n"

echo -e "1. System Overview - Overall system health and performance"
echo -e "2. Agent Performance - AI agent task monitoring"
echo -e "3. Sync Pipeline - Zoho integration metrics"
echo -e "4. Error Tracking - Comprehensive error monitoring"
echo -e "5. Business Metrics - KPIs and business analytics\n"

# Display useful commands
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Useful Commands${NC}"
echo -e "${BLUE}=================================${NC}\n"

echo -e "View logs:          docker-compose logs -f"
echo -e "Stop services:      docker-compose down"
echo -e "Restart services:   docker-compose restart"
echo -e "View metrics:       curl http://localhost:9090/api/v1/targets\n"

# Check if application is running
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Application Status${NC}"
echo -e "${BLUE}=================================${NC}\n"

if curl -sf "http://localhost:8000/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Sergas application is running${NC}"
    echo -e "  Metrics endpoint: http://localhost:8000/metrics\n"
else
    echo -e "${YELLOW}⚠ Sergas application is not running${NC}"
    echo -e "  Start the application to see full metrics\n"
fi

echo -e "${GREEN}Monitoring stack started successfully!${NC}\n"
