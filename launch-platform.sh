#!/bin/bash

echo "🚀 Launching OrbitAgents Full Stack Platform..."

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Kill existing processes
echo "🔧 Cleaning up existing processes..."
pkill -f "python.*8080" 2>/dev/null || true
pkill -f "vite.*300" 2>/dev/null || true
sleep 2

# Start backend
echo "🐍 Starting Backend API (Python Flask)..."
cd api
python index.py &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if check_port 8080; then
        echo "✅ Backend started successfully on port 8080"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start"
        exit 1
    fi
    sleep 1
done

# Start frontend
echo "⚛️  Starting Frontend (React + Vite)..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
for i in {1..30}; do
    if check_port 3001; then
        echo "✅ Frontend started successfully on port 3001"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Frontend failed to start"
        exit 1
    fi
    sleep 1
done

# Test endpoints
echo "🧪 Testing API endpoints..."
backend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
backend_root=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)
backend_demo=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/demo)

if [ "$backend_health" = "200" ] && [ "$backend_root" = "200" ] && [ "$backend_demo" = "200" ]; then
    echo "✅ All API endpoints are working"
else
    echo "⚠️  Some API endpoints may not be working (Health: $backend_health, Root: $backend_root, Demo: $backend_demo)"
fi

# Display URLs
echo ""
echo "🎉 OrbitAgents Platform is now running!"
echo ""
echo "📱 Frontend:          http://localhost:3001"
echo "🔧 Backend API:       http://localhost:8080"
echo "📊 API Root:          http://localhost:8080/"
echo "🩺 Health Check:      http://localhost:8080/health"
echo "🎮 Demo Endpoint:     http://localhost:8080/api/demo"
echo ""
echo "📊 Monitoring Dashboard (if available): http://localhost:9090"
echo ""
echo "🔧 To stop the servers:"
echo "   Frontend PID: $FRONTEND_PID"
echo "   Backend PID:  $BACKEND_PID"
echo "   Kill command: kill $FRONTEND_PID $BACKEND_PID"
echo ""
echo "📝 To access logs:"
echo "   Backend logs: tail -f api.log"
echo "   Frontend logs: Check terminal output"
echo ""

# Optional: Start monitoring dashboard
if [ -f "../monitoring_dashboard.py" ]; then
    echo "🚀 Starting monitoring dashboard..."
    cd ..
    python monitoring_dashboard.py &
    MONITOR_PID=$!
    echo "📊 Monitoring dashboard started on port 9090 (PID: $MONITOR_PID)"
fi

echo "✨ Ready to use! Open http://localhost:3001 in your browser"

# Keep script running
echo "🔄 Press Ctrl+C to stop all services"
wait
