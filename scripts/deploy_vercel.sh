#!/bin/bash

# OrbitAgents Vercel Deployment Script
# This script deploys both frontend and backend to Vercel

set -e

echo "🚀 Deploying OrbitAgents to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Change to the project root directory
cd "$(dirname "$0")/.."

# Login to Vercel (if not already logged in)
echo "🔐 Checking Vercel authentication..."
vercel whoami || vercel login

# Build the frontend first
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Set up environment variables for Vercel
echo "⚙️ Setting up environment variables..."

# Get the current timestamp for unique deployment
TIMESTAMP=$(date +%s)
DEPLOYMENT_ID="orbitagents-${TIMESTAMP}"

# Production environment variables
echo "Setting production environment variables..."
vercel env add DATABASE_URL production <<< "postgresql://user:password@localhost:5432/orbitagents"
vercel env add REDIS_URL production <<< "redis://localhost:6379"
vercel env add JWT_SECRET production <<< "your-super-secret-jwt-key-change-in-production"

# Preview environment variables
echo "Setting preview environment variables..."
vercel env add DATABASE_URL preview <<< "postgresql://user:password@localhost:5432/orbitagents"
vercel env add REDIS_URL preview <<< "redis://localhost:6379"
vercel env add JWT_SECRET preview <<< "your-super-secret-jwt-key-change-in-production"

# Development environment variables
echo "Setting development environment variables..."
vercel env add DATABASE_URL development <<< "postgresql://user:password@localhost:5432/orbitagents"
vercel env add REDIS_URL development <<< "redis://localhost:6379"
vercel env add JWT_SECRET development <<< "your-super-secret-jwt-key-change-in-production"

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod --yes

# Get the deployment URL
DEPLOYMENT_URL=$(vercel --prod --yes 2>&1 | grep -o 'https://[^[:space:]]*' | head -1)

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your OrbitAgents application is now live!"
echo "� Frontend: ${DEPLOYMENT_URL}"
echo "🔗 API: ${DEPLOYMENT_URL}/api"
echo "📖 API Docs: ${DEPLOYMENT_URL}/api/docs"
echo ""
echo "📊 Next steps:"
echo "1. Set up a production database (PostgreSQL)"
echo "2. Set up Redis for caching"
echo "3. Update environment variables with production values"
echo "4. Test the full application workflow"
echo ""
echo "🔧 For local development:"
echo "- Run 'make start-free' to start the full stack locally"
echo "- Visit http://localhost:3001 for the local version"
echo ""
echo "🎯 Test your deployment:"
echo "curl ${DEPLOYMENT_URL}/api/health"
echo "curl ${DEPLOYMENT_URL}/api/auth/health"
echo "curl ${DEPLOYMENT_URL}/api/query/health"
