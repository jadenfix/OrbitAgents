#!/bin/bash

# OrbitAgents Full Stack Development Launcher
# Starts both frontend and backend with proper port configuration

set -e

echo "🚀 Starting OrbitAgents Full Stack Development Environment"
echo "=========================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null; then
        echo -e "${YELLOW}⚠️  Port $1 is in use. Attempting to free it...${NC}"
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
        sleep 2
        if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null; then
            echo "❌ Could not free port $1. Please manually kill the process using that port."
            return 1
        fi
    fi
    return 0
}

# Check and free ports
echo -e "${BLUE}🔍 Checking ports...${NC}"
check_port 3000 || exit 1  # Frontend
check_port 8080 || exit 1  # API

# Start API server in background
echo -e "${BLUE}🐍 Starting Python API server on port 8080...${NC}"
cd api
PORT=8080 python3 index.py &
API_PID=$!
cd ..

# Wait for API to start
echo -e "${YELLOW}⏳ Waiting for API server to start...${NC}"
sleep 3

# Check if API started successfully
if curl -s http://localhost:8080/health >/dev/null; then
    echo -e "${GREEN}✅ API server started successfully!${NC}"
else
    echo "❌ API server failed to start"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Start frontend development server
echo -e "${BLUE}⚛️  Starting React frontend on port 3000...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

echo ""
echo -e "${GREEN}🎉 OrbitAgents Development Environment Ready!${NC}"
echo "=============================================="
echo ""
echo "📊 Available Services:"
echo -e "  ${BLUE}• Frontend (React):${NC} http://localhost:3000"
echo -e "  ${BLUE}• API Server (Flask):${NC} http://localhost:8080"
echo -e "  ${BLUE}• Health Check:${NC} http://localhost:8080/health"
echo -e "  ${BLUE}• Demo Endpoint:${NC} http://localhost:8080/api/demo"
echo -e "  ${BLUE}• API Workflows:${NC} http://localhost:8080/api/browser-agent/workflows"
echo ""
echo -e "${YELLOW}🛠️  Development Commands:${NC}"
echo "  npm run health          # Check API health"
echo "  npm run validate        # Run validation tests"
echo "  npm run monitor         # Start monitoring dashboard"
echo ""
echo -e "${GREEN}🌟 Ready to build the future of AI browser automation!${NC}"
echo ""
echo "📝 Logs will appear below. Press Ctrl+C to stop all services."
echo "=============================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $API_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✅ All services stopped.${NC}"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Keep script running and show logs
wait
