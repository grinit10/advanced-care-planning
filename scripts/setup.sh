#!/usr/bin/env bash
#
# Advanced Care Planning — Local Setup Script
# Run this script to start everything: LiveKit, Redis, Agent, and Frontend
#
# Usage: bash scripts/setup.sh
#        or: ./scripts/setup.sh
#

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo "  Advanced Care Planning — Voice AI"
echo "  Local Setup"
echo -e "========================================${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Check Docker
echo -e "${YELLOW}[1/5] Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "  ${GREEN}✅ Docker is installed: $(docker --version)${NC}"
else
    echo -e "  ${RED}❌ Docker is not installed!${NC}"
    echo "  Please download and install Docker Desktop from:"
    echo "  https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check if Docker is running
if docker info &> /dev/null; then
    echo -e "  ${GREEN}✅ Docker Engine is running${NC}"
else
    echo -e "  ${RED}❌ Docker Engine is not running.${NC}"
    echo "  Please open Docker Desktop and wait for 'Engine running'."
    exit 1
fi

# Step 2: Check .env file
echo -e "${YELLOW}[2/5] Checking configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "  ${GREEN}✅ .env file found${NC}"
else
    echo -e "  ${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "  ${GREEN}✅ Created .env from .env.example${NC}"
    else
        echo -e "  ${RED}❌ .env.example not found either. Project may be incomplete.${NC}"
        exit 1
    fi
fi

# Check for placeholder values
if grep -q "your-api-key-here\|your-resource-name" .env 2>/dev/null; then
    echo -e "  ${YELLOW}⚠️  Your .env file still has placeholder values!${NC}"
    echo "  Opening .env for editing — replace the placeholders with your Azure OpenAI credentials."
    echo ""
    echo -e "  ${CYAN}Your Azure OpenAI endpoint looks like: https://YOUR-RESOURCE.openai.azure.com${NC}"
    echo -e "  ${CYAN}Your Azure OpenAI key looks like:      abc123def456...${NC}"
    echo ""
    read -p "  Press Enter AFTER you've saved the file to continue..."
else
    echo -e "  ${GREEN}✅ .env file looks configured${NC}"
fi

# Step 3: Start Docker Compose
echo -e "${YELLOW}[3/5] Starting services with Docker Compose...${NC}"
echo "  This will download images and start:"
echo "  • Redis (message broker)"
echo "  • LiveKit Server (WebRTC media)"
echo "  • Voice Agent (AI processing)"
echo "  • Token Server (authentication)"
echo "  • Frontend (web interface)"
echo ""

docker compose up -d

if [ $? -ne 0 ]; then
    echo -e "  ${RED}❌ Failed to start services!${NC}"
    echo "  Check the error above. Make sure Docker Desktop is running."
    exit 1
fi

echo -e "  ${GREEN}✅ Services started!${NC}"
echo ""

# Step 4: Wait for services to be healthy
echo -e "${YELLOW}[4/5] Waiting for services to be ready...${NC}"
sleep 3

MAX_RETRIES=12
READY=false
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null | grep -q 200; then
        READY=true
        break
    fi
    echo -n "  ."
    sleep 2
done
echo ""

if [ "$READY" = true ]; then
    echo -e "  ${GREEN}✅ Frontend is ready!${NC}"
else
    echo -e "  ${YELLOW}⚠️  Frontend is taking longer than expected.${NC}"
    echo "  It may still be starting up. Check: docker compose logs frontend"
fi

# Step 5: Open browser
echo -e "${YELLOW}[5/5] Opening the app...${NC}"
case "$(uname -s)" in
    Darwin) open "http://localhost:5173" 2>/dev/null || true ;;
    Linux)  xdg-open "http://localhost:5173" 2>/dev/null || true ;;
esac
echo -e "  ${GREEN}✅ App should be opening at http://localhost:5173${NC}"
echo ""

echo -e "${CYAN}========================================"
echo "  All set! Here's what you can do:"
echo -e "========================================${NC}"
echo ""
echo "  🌐 Open the app:     http://localhost:5173"
echo ""
echo "  📋 View agent logs:  docker compose logs -f agent"
echo "  🛑 Stop everything:  docker compose down"
echo "  ▶️  Restart later:   docker compose up -d"
echo ""
echo "  Need help? Check the README.md file."