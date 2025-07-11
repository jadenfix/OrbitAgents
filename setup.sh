#!/bin/bash

echo "🚀 Setting up OrbitAgents Full Stack Application"
echo "=============================================="

# Install root dependencies
echo "📦 Installing root dependencies..."
npm install

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend && npm install && cd ..

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r api/requirements.txt --user

echo "✅ Setup complete!"
echo ""
echo "🎯 Now run: npm run dev"
echo "🌐 Frontend: http://localhost:3000"
echo "📡 API: http://localhost:5001"
echo ""
echo "🔧 Available commands:"
echo "  npm run dev       - Start both frontend and backend"
echo "  npm run frontend  - Start only frontend"
echo "  npm run backend   - Start only backend"
echo "  npm run build     - Build frontend for production"
