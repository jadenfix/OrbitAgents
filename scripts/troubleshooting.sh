#!/bin/bash

# OrbitAgents Troubleshooting and Quick Fix Script
# Automatically diagnose and fix common development issues

set -euo pipefail

echo "🔧 OrbitAgents Troubleshooting & Quick Fix Automation"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from project root
if [[ ! -f "package.json" ]] || [[ ! -d "api" ]] || [[ ! -d "frontend" ]]; then
    log_error "Please run this script from the OrbitAgents project root directory"
    exit 1
fi

# Function to check and fix Node.js environment
check_node_environment() {
    log_info "Checking Node.js environment..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
        return 1
    fi
    
    NODE_VERSION=$(node --version | sed 's/v//')
    REQUIRED_VERSION="18.0.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        log_error "Node.js version $NODE_VERSION is too old. Required: $REQUIRED_VERSION+"
        return 1
    fi
    
    log_success "Node.js version $NODE_VERSION is compatible"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm not found. Please install npm"
        return 1
    fi
    
    log_success "npm is available"
    return 0
}

# Function to check and fix Python environment
check_python_environment() {
    log_info "Checking Python environment..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3.9+ from https://python.org/"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    REQUIRED_VERSION="3.9.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        log_error "Python version $PYTHON_VERSION is too old. Required: $REQUIRED_VERSION+"
        return 1
    fi
    
    log_success "Python version $PYTHON_VERSION is compatible"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 not found. Please install pip"
        return 1
    fi
    
    log_success "pip3 is available"
    return 0
}

# Function to fix dependency issues
fix_dependencies() {
    log_info "Fixing dependency issues..."
    
    # Clean and reinstall root dependencies
    if [[ -f "package-lock.json" ]]; then
        log_info "Cleaning root package-lock.json..."
        rm -f package-lock.json
    fi
    
    if [[ -d "node_modules" ]]; then
        log_info "Cleaning root node_modules..."
        rm -rf node_modules
    fi
    
    log_info "Installing root dependencies..."
    npm install
    
    # Fix frontend dependencies
    if [[ -d "frontend" ]]; then
        cd frontend
        
        if [[ -f "package-lock.json" ]]; then
            log_info "Cleaning frontend package-lock.json..."
            rm -f package-lock.json
        fi
        
        if [[ -d "node_modules" ]]; then
            log_info "Cleaning frontend node_modules..."
            rm -rf node_modules
        fi
        
        log_info "Installing frontend dependencies..."
        npm install
        cd ..
    fi
    
    # Fix Python dependencies
    if [[ -d "api" ]]; then
        log_info "Setting up Python virtual environment..."
        
        if [[ ! -d "venv" ]]; then
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        
        log_info "Upgrading pip..."
        pip install --upgrade pip
        
        if [[ -f "api/requirements.txt" ]]; then
            log_info "Installing Python dependencies..."
            pip install -r api/requirements.txt
        fi
        
        # Install Playwright browsers if needed
        if pip list | grep -q playwright; then
            log_info "Installing Playwright browsers..."
            playwright install
        fi
        
        deactivate
    fi
    
    log_success "Dependencies fixed successfully"
}

# Function to check and fix port conflicts
check_port_conflicts() {
    log_info "Checking for port conflicts..."
    
    PORTS=(3000 5000 8000 11434)
    
    for port in "${PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "Port $port is in use"
            log_info "Process using port $port:"
            lsof -Pi :$port -sTCP:LISTEN
            
            read -p "Kill process on port $port? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                lsof -ti:$port | xargs kill -9
                log_success "Process on port $port killed"
            fi
        else
            log_success "Port $port is available"
        fi
    done
}

# Function to check and fix environment variables
check_environment_variables() {
    log_info "Checking environment variables..."
    
    # Check for .env files
    ENV_FILES=(".env" "api/.env" "frontend/.env")
    
    for env_file in "${ENV_FILES[@]}"; do
        if [[ -f "$env_file" ]]; then
            log_success "Found $env_file"
        else
            log_warning "$env_file not found"
            
            # Create basic .env files
            case $env_file in
                ".env")
                    cat > .env << EOF
# OrbitAgents Root Environment Variables
NODE_ENV=development
PYTHONPATH=./api
EOF
                    log_success "Created basic $env_file"
                    ;;
                "api/.env")
                    cat > api/.env << EOF
# API Environment Variables
FLASK_ENV=development
FLASK_DEBUG=true
CORS_ORIGINS=http://localhost:3000
OLLAMA_BASE_URL=http://localhost:11434
EOF
                    log_success "Created basic $env_file"
                    ;;
                "frontend/.env")
                    cat > frontend/.env << EOF
# Frontend Environment Variables
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000
EOF
                    log_success "Created basic $env_file"
                    ;;
            esac
        fi
    done
}

# Function to check Ollama setup
check_ollama() {
    log_info "Checking Ollama setup..."
    
    if ! command -v ollama &> /dev/null; then
        log_warning "Ollama not found. Installing Ollama..."
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install ollama
            else
                log_error "Please install Homebrew or download Ollama from https://ollama.ai/"
                return 1
            fi
        else
            # Linux
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    fi
    
    # Check if Ollama service is running
    if ! pgrep -x "ollama" > /dev/null; then
        log_warning "Ollama service not running. Starting Ollama..."
        ollama serve &
        sleep 5
    fi
    
    # Check if models are pulled
    MODELS=("phi3:mini" "llama3.1:8b")
    
    for model in "${MODELS[@]}"; do
        if ollama list | grep -q "$model"; then
            log_success "Ollama model $model is available"
        else
            log_warning "Ollama model $model not found. Pulling..."
            ollama pull "$model"
        fi
    done
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check if virtual environment exists and activate it
    if [[ -d "venv" ]]; then
        source venv/bin/activate
        
        # Test Python imports
        log_info "Testing Python imports..."
        python3 -c "
import sys
import flask
import playwright
import autogen
import langgraph
import chromadb
import sentence_transformers
print('All Python imports successful')
" && log_success "Python imports working" || log_error "Python import issues detected"
        
        deactivate
    fi
    
    # Test Node.js project
    if [[ -d "frontend" ]]; then
        cd frontend
        log_info "Testing frontend build..."
        npm run build > /dev/null 2>&1 && log_success "Frontend build successful" || log_error "Frontend build issues detected"
        cd ..
    fi
    
    # Test API endpoints
    if [[ -f "api/index.py" ]]; then
        log_info "Testing API health..."
        source venv/bin/activate
        
        # Start API in background
        cd api
        python index.py &
        API_PID=$!
        cd ..
        
        sleep 3
        
        # Test health endpoint
        if curl -s http://localhost:5000/health > /dev/null; then
            log_success "API health check passed"
        else
            log_error "API health check failed"
        fi
        
        # Kill background API
        kill $API_PID > /dev/null 2>&1
        deactivate
    fi
}

# Function to generate diagnostic report
generate_diagnostic_report() {
    log_info "Generating diagnostic report..."
    
    REPORT_FILE="diagnostic_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
OrbitAgents Diagnostic Report
Generated: $(date)
============================

System Information:
- OS: $(uname -s)
- Architecture: $(uname -m)
- Node.js: $(node --version 2>/dev/null || echo "Not installed")
- npm: $(npm --version 2>/dev/null || echo "Not installed")
- Python: $(python3 --version 2>/dev/null || echo "Not installed")
- pip: $(pip3 --version 2>/dev/null || echo "Not installed")

Project Structure:
$(find . -maxdepth 2 -type f -name "*.json" -o -name "*.py" -o -name "*.tsx" -o -name "*.ts" | sort)

Environment Files:
$(find . -name ".env*" | sort)

Python Virtual Environment:
$(if [[ -d "venv" ]]; then echo "EXISTS"; else echo "NOT FOUND"; fi)

Node Modules:
$(if [[ -d "node_modules" ]]; then echo "ROOT: EXISTS"; else echo "ROOT: NOT FOUND"; fi)
$(if [[ -d "frontend/node_modules" ]]; then echo "FRONTEND: EXISTS"; else echo "FRONTEND: NOT FOUND"; fi)

Port Status:
$(lsof -i :3000 -i :5000 -i :8000 -i :11434 2>/dev/null || echo "No processes found on standard ports")

Ollama Status:
$(ollama --version 2>/dev/null || echo "Not installed")
$(ollama list 2>/dev/null || echo "Cannot list models")

Recent Errors:
$(tail -n 20 /tmp/orbit_errors.log 2>/dev/null || echo "No error log found")
EOF
    
    log_success "Diagnostic report generated: $REPORT_FILE"
}

# Main troubleshooting workflow
main() {
    log_info "Starting comprehensive troubleshooting..."
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fix-deps)
                fix_dependencies
                exit 0
                ;;
            --check-ports)
                check_port_conflicts
                exit 0
                ;;
            --setup-ollama)
                check_ollama
                exit 0
                ;;
            --health-check)
                run_health_checks
                exit 0
                ;;
            --report)
                generate_diagnostic_report
                exit 0
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --fix-deps      Fix dependency issues"
                echo "  --check-ports   Check and fix port conflicts"
                echo "  --setup-ollama  Setup Ollama and models"
                echo "  --health-check  Run health checks"
                echo "  --report        Generate diagnostic report"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
        shift
    done
    
    # Run all checks and fixes if no specific option provided
    log_info "Running comprehensive troubleshooting..."
    
    check_node_environment || exit 1
    check_python_environment || exit 1
    check_environment_variables
    check_port_conflicts
    fix_dependencies
    check_ollama
    run_health_checks
    generate_diagnostic_report
    
    log_success "Troubleshooting completed!"
    log_info "If issues persist, check the diagnostic report and run: npm run dev"
}

# Run main function
main "$@"
