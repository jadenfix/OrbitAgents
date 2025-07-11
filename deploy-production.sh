#!/bin/bash

# OrbitAgents Production Deployment Script
# This script deploys the full OrbitAgents platform with production optimizations

set -e

echo "🚀 OrbitAgents Production Deployment"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_PORT=${FRONTEND_PORT:-3000}
API_PORT=${API_PORT:-8080}
MONITORING_PORT=${MONITORING_PORT:-9090}

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
fi
print_status "Node.js found: $(node --version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi
print_status "Python found: $(python3 --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
fi
print_status "npm found: $(npm --version)"

# Stop existing processes
echo ""
echo "🛑 Stopping existing processes..."
pkill -f "vite.*$FRONTEND_PORT" 2>/dev/null || true
pkill -f "flask.*run.*$API_PORT" 2>/dev/null || true
pkill -f "python.*monitoring_dashboard.py" 2>/dev/null || true
print_status "Stopped existing processes"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."

# Install root dependencies
npm install
print_status "Root dependencies installed"

# Install frontend dependencies
cd frontend
npm install
print_status "Frontend dependencies installed"

# Install Python dependencies
cd ../api
pip install -r requirements.txt
print_status "Python dependencies installed"

cd ..

# Build frontend for production
echo ""
echo "🏗️  Building frontend for production..."
cd frontend
npm run build
print_status "Frontend built successfully"
cd ..

# Run production tests
echo ""
echo "🧪 Running production tests..."
python tests/frontend_e2e_tests.py
print_status "Production tests completed"

# Start services
echo ""
echo "🚀 Starting production services..."

# Start API server
echo "Starting API server on port $API_PORT..."
cd api
nohup python index.py --port $API_PORT > ../logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > ../logs/api.pid
cd ..

# Wait for API to start
sleep 5

# Test API health
if curl -f http://localhost:$API_PORT/health > /dev/null 2>&1; then
    print_status "API server started successfully on port $API_PORT"
else
    print_error "API server failed to start"
    exit 1
fi

# Start monitoring dashboard
echo "Starting monitoring dashboard on port $MONITORING_PORT..."
nohup python monitoring_dashboard.py --port $MONITORING_PORT > logs/monitoring.log 2>&1 &
MONITORING_PID=$!
echo $MONITORING_PID > logs/monitoring.pid

# Wait for monitoring to start
sleep 3

# Start frontend server
echo "Starting frontend server on port $FRONTEND_PORT..."
cd frontend
nohup npm run preview -- --port $FRONTEND_PORT > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

# Wait for frontend to start
sleep 5

# Test frontend
if curl -f http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
    print_status "Frontend server started successfully on port $FRONTEND_PORT"
else
    print_error "Frontend server failed to start"
    exit 1
fi

# Create service management script
cat > manage_services.sh << 'EOF'
#!/bin/bash

case "$1" in
    status)
        echo "Service Status:"
        echo "==============="
        
        # Check API
        if pgrep -f "python.*index.py" > /dev/null; then
            echo "✅ API Server: Running (PID: $(cat logs/api.pid 2>/dev/null || echo 'unknown'))"
        else
            echo "❌ API Server: Stopped"
        fi
        
        # Check Frontend
        if pgrep -f "vite.*preview" > /dev/null; then
            echo "✅ Frontend: Running (PID: $(cat logs/frontend.pid 2>/dev/null || echo 'unknown'))"
        else
            echo "❌ Frontend: Stopped"
        fi
        
        # Check Monitoring
        if pgrep -f "python.*monitoring_dashboard.py" > /dev/null; then
            echo "✅ Monitoring: Running (PID: $(cat logs/monitoring.pid 2>/dev/null || echo 'unknown'))"
        else
            echo "❌ Monitoring: Stopped"
        fi
        ;;
    stop)
        echo "Stopping all services..."
        pkill -f "python.*index.py" 2>/dev/null || true
        pkill -f "vite.*preview" 2>/dev/null || true
        pkill -f "python.*monitoring_dashboard.py" 2>/dev/null || true
        rm -f logs/*.pid
        echo "All services stopped"
        ;;
    restart)
        $0 stop
        sleep 2
        ./deploy-production.sh
        ;;
    logs)
        echo "Recent logs:"
        echo "============"
        echo "--- API Logs ---"
        tail -n 10 logs/api.log 2>/dev/null || echo "No API logs"
        echo "--- Frontend Logs ---"
        tail -n 10 logs/frontend.log 2>/dev/null || echo "No frontend logs"
        echo "--- Monitoring Logs ---"
        tail -n 10 logs/monitoring.log 2>/dev/null || echo "No monitoring logs"
        ;;
    *)
        echo "Usage: $0 {status|stop|restart|logs}"
        exit 1
        ;;
esac
EOF

chmod +x manage_services.sh

# Create logs directory
mkdir -p logs

# Final deployment report
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
print_info "Frontend URL: http://localhost:$FRONTEND_PORT"
print_info "API URL: http://localhost:$API_PORT"
print_info "Monitoring Dashboard: http://localhost:$MONITORING_PORT"
print_info "API Documentation: http://localhost:$API_PORT/"

echo ""
echo "🔧 Service Management:"
echo "  ./manage_services.sh status   - Check service status"
echo "  ./manage_services.sh stop     - Stop all services"
echo "  ./manage_services.sh restart  - Restart all services"
echo "  ./manage_services.sh logs     - View recent logs"

echo ""
echo "📊 Quick Health Check:"
echo "  Frontend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:$FRONTEND_PORT)"
echo "  API: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:$API_PORT)"
echo "  Monitoring: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:$MONITORING_PORT)"

echo ""
print_status "OrbitAgents is now running in production mode!"
print_info "Visit http://localhost:$FRONTEND_PORT to start using the platform"
