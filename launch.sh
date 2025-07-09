#!/bin/bash

set -e

echo "🚀 LAUNCHING ORBITAGENTS PLATFORM"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_blue() {
    echo -e "${BLUE}[EXEC]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v node >/dev/null 2>&1; then
    print_error "Node.js not found. Please install Node.js first."
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    print_error "npm not found. Please install npm first."
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    print_error "Git not found. Please install Git first."
    exit 1
fi

# Install Vercel CLI
if ! command -v vercel >/dev/null 2>&1; then
    print_status "Installing Vercel CLI..."
    npm install -g vercel
fi

# Setup frontend
print_status "Setting up frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    print_blue "Installing frontend dependencies..."
    npm install
fi

print_blue "Building frontend..."
npm run build

cd ..

# Git operations
print_status "Committing changes to Git..."
git add .
git commit -m "🚀 Launch OrbitAgents platform with optimized Vercel deployment

- Updated vercel.json for better routing and performance
- Created comprehensive API with all endpoints
- Added proper error handling and logging
- Optimized frontend build process
- Ready for production deployment" || print_warning "Nothing to commit"

print_blue "Pushing to GitHub..."
git push origin main

# Deploy to Vercel
print_status "Deploying to Vercel..."
print_blue "Starting Vercel deployment..."
vercel --prod

print_status "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "✅ OrbitAgents platform has been successfully launched!"
echo ""
echo "🔗 Access your application:"
echo "   - Check your Vercel dashboard for the live URL"
echo "   - Frontend: https://your-app.vercel.app"
echo "   - API: https://your-app.vercel.app/api/health"
echo ""
echo "🧪 Test your deployment:"
echo "   curl https://your-app.vercel.app/api/health"
echo "   curl -X POST https://your-app.vercel.app/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"demo\",\"password\":\"demo\"}'"
echo "   curl -X POST https://your-app.vercel.app/api/search -H 'Content-Type: application/json' -d '{\"query\":\"modern apartment\"}'"
echo "   curl https://your-app.vercel.app/api/browser-agent/workflows"
echo ""
echo "📖 Documentation: https://github.com/jadenfix/OrbitAgents"
echo ""
echo "🎯 Next steps:"
echo "   1. Visit your Vercel dashboard to get the live URL"
echo "   2. Test all API endpoints"
echo "   3. Explore the browser agent features"
echo "   4. Set up custom domain (optional)"
echo ""
echo "🔧 For local development:"
echo "   make quick-start"
echo "   npm run dev (in frontend directory)"
echo "   python3 api/index.py (in separate terminal)"
