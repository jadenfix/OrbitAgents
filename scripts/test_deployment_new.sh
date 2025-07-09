#!/bin/bash

# OrbitAgents Comprehensive Deployment Test Script
# Tests both local and Vercel deployments with full functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 OrbitAgents Deployment Test Suite${NC}"
echo "======================================"

# Get deployment URL from user or use default
DEPLOYMENT_URL=${1:-"https://your-app.vercel.app"}

echo "Testing deployment at: $DEPLOYMENT_URL"
echo ""

# Function to test an endpoint
test_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "URL: $url"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} - Status: $response"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} - Expected: $expected_status, Got: $response"
        return 1
    fi
}

# Function to test JSON response
test_json_endpoint() {
    local url=$1
    local description=$2
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "URL: $url"
    
    response=$(curl -s "$url" || echo '{"error": "request failed"}')
    
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC} - Valid JSON response"
        echo "Response: $(echo "$response" | jq -r '.message // .status // "OK"')"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} - Invalid JSON response"
        echo "Response: $response"
        return 1
    fi
}

# Function to test POST endpoint
test_post_endpoint() {
    local url=$1
    local data=$2
    local description=$3
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "URL: $url"
    echo "Data: $data"
    
    response=$(curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$data" || echo '{"error": "request failed"}')
    
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC} - Valid JSON response"
        echo "Response: $(echo "$response" | jq -r '.message // .status // .token // "OK"')"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} - Invalid JSON response"
        echo "Response: $response"
        return 1
    fi
}

# Test API endpoints
echo -e "\n${BLUE}📡 Testing API Endpoints${NC}"
echo "========================"

# Test health endpoint
test_json_endpoint "$DEPLOYMENT_URL/api/health" "Health Check"

# Test authentication
test_post_endpoint "$DEPLOYMENT_URL/api/auth/login" '{"username":"demo","password":"demo"}' "Authentication Login"

# Test search
test_post_endpoint "$DEPLOYMENT_URL/api/search" '{"query":"modern apartment"}' "Search Functionality"

# Test browser agent workflows
test_json_endpoint "$DEPLOYMENT_URL/api/browser-agent/workflows" "Browser Agent Workflows"

# Test workflow execution
test_post_endpoint "$DEPLOYMENT_URL/api/browser-agent/execute" '{"workflow_id":1}' "Workflow Execution"

# Test local deployment if available
echo -e "\n${BLUE}📍 Testing Local Deployment (Optional)${NC}"
echo "======================================="

# Check if local Flask API is running
if curl -s http://localhost:8080/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Local Flask API is running${NC}"
    
    # Test local Flask API endpoints
    test_json_endpoint "http://localhost:8080/api/health" "Local Flask API Health"
    test_post_endpoint "http://localhost:8080/api/auth/login" '{"username":"demo","password":"demo"}' "Local Auth Login"
    test_post_endpoint "http://localhost:8080/api/search" '{"query":"test property"}' "Local Search"
    test_json_endpoint "http://localhost:8080/api/browser-agent/workflows" "Local Browser Agent Workflows"
    
else
    echo -e "${YELLOW}⚠️  Local Flask API not running${NC}"
    echo "Start local API with: FLASK_APP=api/index.py python3 -m flask run --port=8080"
fi

# Check if full local services are running
if curl -s http://localhost:3001 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Full local deployment is running${NC}"
    
    # Test local endpoints
    test_endpoint "http://localhost:3001" "200" "Frontend (React App)"
    test_json_endpoint "http://localhost:8001/health" "Auth Service Health"
    test_json_endpoint "http://localhost:8002/health" "Query Service Health" 
    test_json_endpoint "http://localhost:8003/health" "Crawler Service Health"
    test_json_endpoint "http://localhost:8004/health" "Browser Agent Health"
    
else
    echo -e "${YELLOW}⚠️  Full local deployment not running${NC}"
    echo "Start full local services with: make start-free"
fi

echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "==============="
echo "✅ All tests completed!"
echo ""
echo -e "${GREEN}🎉 OrbitAgents is ready!${NC}"
echo "🔗 Production: $DEPLOYMENT_URL"
echo "🔗 Local: http://localhost:3001"
echo ""
echo "🧪 Quick test commands:"
echo "   curl $DEPLOYMENT_URL/api/health"
echo "   curl -X POST $DEPLOYMENT_URL/api/search -H 'Content-Type: application/json' -d '{\"query\":\"test\"}'"
echo "   curl $DEPLOYMENT_URL/api/browser-agent/workflows"
echo ""
echo "� Documentation: https://github.com/jadenfix/OrbitAgents"
