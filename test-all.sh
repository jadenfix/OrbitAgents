#!/bin/bash

# OrbitAgents Comprehensive Test Suite

echo "🧪 Running OrbitAgents Comprehensive Test Suite"
echo "=============================================="

# Run minimal validation
echo "1. Running minimal validation..."
python3 tests/minimal_validation.py
if [ $? -ne 0 ]; then
    echo "❌ Minimal validation failed"
    exit 1
fi

# Test API endpoints
echo ""
echo "2. Testing API endpoints..."
python3 -c "
import requests
import sys

try:
    # Test health endpoint
    response = requests.get('http://localhost:5000/health', timeout=5)
    if response.status_code == 200:
        print('✅ Health endpoint working')
    else:
        print('❌ Health endpoint failed')
        sys.exit(1)
        
    # Test demo endpoint
    response = requests.get('http://localhost:5000/api/demo', timeout=5)
    if response.status_code == 200:
        print('✅ Demo endpoint working')
    else:
        print('❌ Demo endpoint failed')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ API tests failed: {e}')
    print('💡 Make sure the API server is running (./start-dev.sh)')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ API endpoint tests failed"
    exit 1
fi

echo ""
echo "🎉 All tests passed! OrbitAgents is ready for development."
