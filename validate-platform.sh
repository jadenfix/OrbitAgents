#!/bin/bash

echo "🧪 OrbitAgents Platform Validation Suite"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test an endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $response, expected $expected_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test JSON endpoint and extract data
test_json_endpoint() {
    local name=$1
    local url=$2
    local expected_field=$3
    
    echo -n "Testing $name (JSON)... "
    
    response=$(curl -s "$url" 2>/dev/null)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$http_code" = "200" ]; then
        if echo "$response" | jq -e ".$expected_field" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code, has $expected_field)"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${YELLOW}⚠️  PARTIAL${NC} (HTTP $http_code, missing $expected_field)"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo ""
echo "🔍 Backend API Tests"
echo "-------------------"

# Test backend endpoints
test_endpoint "Backend Root" "http://localhost:8080/"
test_json_endpoint "Health Check" "http://localhost:8080/health" "status"
test_json_endpoint "Demo Endpoint" "http://localhost:8080/api/demo" "message"

echo ""
echo "🔍 Frontend Tests"
echo "----------------"

# Test frontend
test_endpoint "Frontend Root" "http://localhost:3001/"

# Test if frontend serves static assets
test_endpoint "Frontend Assets" "http://localhost:3001/vite.svg" 200

echo ""
echo "🔍 Cross-Integration Tests"
echo "-------------------------"

# Test API through frontend proxy
test_endpoint "Proxied Health Check" "http://localhost:3001/api/health"
test_endpoint "Proxied Demo" "http://localhost:3001/api/demo"

echo ""
echo "🔍 Detailed API Response Tests"
echo "------------------------------"

echo "📊 Backend Root Response:"
curl -s http://localhost:8080/ | jq . 2>/dev/null || echo "❌ Invalid JSON response"

echo ""
echo "🩺 Health Check Response:"
curl -s http://localhost:8080/health | jq . 2>/dev/null || echo "❌ Invalid JSON response"

echo ""
echo "🎮 Demo Response:"
curl -s http://localhost:8080/api/demo | jq . 2>/dev/null || echo "❌ Invalid JSON response"

echo ""
echo "📋 Test Summary"
echo "==============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}All tests passed! OrbitAgents platform is working correctly.${NC}"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Frontend: http://localhost:3001"
    echo "   Backend:  http://localhost:8080"
    echo ""
    echo "✨ You can now use the platform!"
    exit 0
else
    echo -e "\n⚠️  ${YELLOW}Some tests failed. Please check the services.${NC}"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Ensure both frontend and backend are running"
    echo "   2. Check for port conflicts"
    echo "   3. Review server logs for errors"
    echo "   4. Try restarting with: ./launch-platform.sh"
    exit 1
fi
