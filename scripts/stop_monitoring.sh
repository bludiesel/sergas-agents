#!/bin/bash
# Sergas Super Account Manager - Monitoring Stack Shutdown Script
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

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}Sergas Monitoring Stack Shutdown${NC}"
echo -e "${BLUE}==================================${NC}\n"

# Change to monitoring directory
cd "$MONITORING_DIR"

# Ask for confirmation
echo -e "${YELLOW}This will stop all monitoring services.${NC}"
read -p "Continue? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Shutdown cancelled${NC}"
    exit 0
fi

# Stop services
echo -e "\n${YELLOW}Stopping monitoring services...${NC}"
docker-compose down

echo -e "${GREEN}✓ All monitoring services stopped${NC}\n"

# Ask about data cleanup
echo -e "${YELLOW}Do you want to remove monitoring data volumes?${NC}"
echo -e "${RED}WARNING: This will delete all metrics history!${NC}"
read -p "Remove volumes? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}Removing data volumes...${NC}"
    docker-compose down -v
    echo -e "${GREEN}✓ Data volumes removed${NC}\n"
else
    echo -e "\n${BLUE}Data volumes preserved${NC}\n"
fi

echo -e "${GREEN}Monitoring stack shutdown complete${NC}\n"
