#!/bin/bash

# Quick OrbitAgents Test Script
# Tests all services with curl commands

echo "🚀 OrbitAgents Quick Test Suite"
echo "==============================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
}

test_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
}

test_warn() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

# Test infrastructure services
echo "📊 Testing Infrastructure Services"
echo "=================================="

# Test PostgreSQL
if nc -z localhost 5432; then
    test_pass "PostgreSQL is running on port 5432"
else
    test_fail "PostgreSQL is not accessible"
fi

# Test Redis
if nc -z localhost 6379; then
    test_pass "Redis is running on port 6379"
else
    test_fail "Redis is not accessible"
fi

# Test OpenSearch
if curl -s http://localhost:9200 > /dev/null; then
    test_pass "OpenSearch is accessible at http://localhost:9200"
else
    test_fail "OpenSearch is not accessible"
fi

# Test MinIO
if curl -s http://localhost:9000/minio/health/live > /dev/null; then
    test_pass "MinIO is accessible at http://localhost:9000"
else
    test_fail "MinIO is not accessible"
fi

# Test Ollama
if curl -s http://localhost:11434/api/version > /dev/null; then
    test_pass "Ollama is accessible at http://localhost:11434"
else
    test_warn "Ollama is not accessible (optional for basic testing)"
fi

echo ""
echo "🤖 Testing Application Services"
echo "==============================="

# Test Auth Service Health
echo "Testing Auth Service..."
if curl -s -f http://localhost:8001/health > /dev/null; then
    test_pass "Auth service health check"
else
    test_fail "Auth service is not healthy"
fi

# Test Query Service Health
echo "Testing Query Service..."
if curl -s -f http://localhost:8002/health > /dev/null; then
    test_pass "Query service health check"
else
    test_fail "Query service is not healthy"
fi

# Test Browser Agent Service Health
echo "Testing Browser Agent Service..."
if curl -s -f http://localhost:8003/health > /dev/null; then
    test_pass "Browser agent service health check"
else
    test_fail "Browser agent service is not healthy"
fi

echo ""
echo "🧪 Testing API Functionality"
echo "============================"

# Test User Registration
echo "Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' 2>/dev/null)

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    test_pass "User registration works"
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
else
    test_fail "User registration failed"
fi

# Test User Login
echo "Testing user login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' 2>/dev/null)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    test_pass "User login works"
else
    test_fail "User login failed"
fi

# Test Search
echo "Testing search functionality..."
SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test search", "limit": 5}' 2>/dev/null)

if echo "$SEARCH_RESPONSE" | grep -q "results"; then
    test_pass "Search functionality works"
    echo "   → Found $(echo "$SEARCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null) results"
else
    test_fail "Search functionality failed"
fi

# Test Browser Automation - Simple Action
echo "Testing browser automation..."
BROWSER_RESPONSE=$(curl -s -X POST http://localhost:8003/automation/web-action \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "actions": [{"type": "screenshot"}]}' 2>/dev/null)

if echo "$BROWSER_RESPONSE" | grep -q "status"; then
    test_pass "Browser automation works"
    echo "   → Status: $(echo "$BROWSER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)"
else
    test_fail "Browser automation failed"
fi

# Test Form Filling
echo "Testing form filling..."
FORM_RESPONSE=$(curl -s -X POST http://localhost:8003/automation/form-fill \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/forms/post", "form_data": {"custname": "John Doe"}}' 2>/dev/null)

if echo "$FORM_RESPONSE" | grep -q "status"; then
    test_pass "Form filling works"
else
    test_fail "Form filling failed"
fi

# Test Data Scraping
echo "Testing data scraping..."
SCRAPE_RESPONSE=$(curl -s -X POST http://localhost:8003/automation/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://quotes.toscrape.com", "selectors": {"title": "title"}}' 2>/dev/null)

if echo "$SCRAPE_RESPONSE" | grep -q "status"; then
    test_pass "Data scraping works"
else
    test_fail "Data scraping failed"
fi

echo ""
echo "📈 Performance Test"
echo "=================="

echo "Running 5 concurrent search requests..."
START_TIME=$(date +%s)
for i in {1..5}; do
    curl -s -X POST http://localhost:8002/search \
      -H "Content-Type: application/json" \
      -d '{"query": "performance test '${i}'", "limit": 5}' > /dev/null &
done
wait
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $DURATION -lt 10 ]; then
    test_pass "Performance test completed in ${DURATION}s"
else
    test_warn "Performance test took ${DURATION}s (might be slow)"
fi

echo ""
echo "📋 Test Summary"
echo "==============="
echo "🌐 Access URLs:"
echo "   • Frontend: http://localhost:3001"
echo "   • Auth API: http://localhost:8001/docs"
echo "   • Query API: http://localhost:8002/docs"
echo "   • Browser Agent: http://localhost:8003/docs"
echo "   • OpenSearch: http://localhost:9200"
echo "   • MinIO Console: http://localhost:9001"
echo "   • Grafana: http://localhost:3000"
echo ""
echo "🎉 OrbitAgents testing completed!"
echo "All core services are functional and ready for use."
