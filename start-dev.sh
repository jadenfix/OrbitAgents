#!/bin/bash

# OrbitAgents Development Startup Script

echo "🚀 Starting OrbitAgents Development Environment"

# Check if ports are available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null; then
        echo "Port $1 is in use. Please free it or modify the configuration."
        return 1
    fi
    return 0
}

# Check ports
check_port 3000 || exit 1  # Frontend
check_port 8080 || exit 1  # API (changed from 5000 to avoid macOS AirPlay)

# Start API in background
echo "Starting API server on port 8080..."
cd api && PORT=8080 python3 index.py &
API_PID=$!

# Wait a moment for API to start
sleep 2

# Check if API started successfully
if curl -s http://localhost:8080/health >/dev/null; then
    echo "✅ API server started successfully"
else
    echo "❌ API server failed to start"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 OrbitAgents Development Environment Ready!"
echo ""
echo "📊 Services:"
echo "  • API Server: http://localhost:8080"
echo "  • Health Check: http://localhost:8080/health"
echo "  • Demo Endpoint: http://localhost:8080/api/demo"
echo ""
echo "🛠️  For frontend development:"
echo "  cd frontend && npm install && npm run dev"
echo ""
echo "📝 Logs will appear below. Press Ctrl+C to stop all services."
echo ""

# Keep script running and show API logs
wait $API_PID
