# 🆓 Free Tier Setup Guide

## Overview
This guide helps you deploy OrbitAgents using completely free services and open-source alternatives.

## 🗄️ Database Options

### Option 1: PostgreSQL (Recommended)
```bash
# Docker setup (local development)
docker run --name orbit-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:15

# Or use free cloud PostgreSQL
# - Supabase: 500MB free
# - Railway: 1GB free
# - Neon: 512MB free
```

### Option 2: SQLite (Ultra-lightweight)
```bash
# No setup required - file-based database
export DATABASE_URL="sqlite:///./orbit.db"
```

## 🔍 Search Engine

### OpenSearch (Free Elasticsearch Alternative)
```bash
# Docker setup
docker run --name orbit-opensearch -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" opensearchproject/opensearch:2.11.0

# Or use free cloud alternatives:
# - OpenSearch Service (AWS free tier)
# - Elasticsearch (Elastic Cloud free tier)
```

## 📦 Object Storage

### Option 1: MinIO (Free S3-compatible)
```bash
# Docker setup
docker run --name orbit-minio -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=admin" -e "MINIO_ROOT_PASSWORD=password123" minio/minio server /data --console-address ":9001"
```

### Option 2: Local Filesystem
```bash
# Just use local directories
export STORAGE_TYPE="filesystem"
export STORAGE_PATH="/app/data"
```

## 🚀 Deployment Options

### Option 1: Local Development (Kind)
```bash
# Install kind (Kubernetes in Docker)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster --name orbit-agents
```

### Option 2: Free Cloud Tiers
- **Google Cloud Run**: 2 million requests/month free
- **AWS Lambda**: 1 million requests/month free
- **Vercel**: Free for hobby projects
- **Railway**: $5/month credit free
- **Render**: Free tier with 750 hours/month

## 🤖 AI/ML Services

### Ollama (Free Local LLMs)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download free models
ollama pull llama2:7b
ollama pull codellama:7b
```

### spaCy (Free NLP)
```bash
# Already integrated in the codebase
pip install spacy
python -m spacy download en_core_web_sm
```

## 📊 Monitoring Stack

### Prometheus + Grafana (Free)
```bash
# Docker compose for monitoring
docker run --name orbit-prometheus -p 9090:9090 prom/prometheus
docker run --name orbit-grafana -p 3000:3000 grafana/grafana
```

## 🔄 CI/CD

### GitHub Actions (Free for Open Source)
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## 🌐 Browser Automation

### Playwright (Free)
```bash
# Install Playwright
pip install playwright
playwright install
```

### Puppeteer (Free)
```bash
# Install Puppeteer
npm install puppeteer
```

## 📡 Message Queue

### Redis (Free)
```bash
# Docker setup
docker run --name orbit-redis -p 6379:6379 -d redis:7

# Or use free cloud Redis:
# - Redis Labs: 30MB free
# - Upstash: 10K commands/day free
```

## 🔐 Authentication

### JWT (Free)
```bash
# No external service needed
# Self-contained JWT tokens
```

## 📈 Free Tier Limits Summary

| Service | Free Tier | Upgrade Path |
|---------|-----------|-------------|
| PostgreSQL | 500MB - 1GB | $20/month for 10GB |
| OpenSearch | 750 hours/month | $50/month for production |
| MinIO | Unlimited local | $10/month for cloud |
| Monitoring | Local unlimited | $9/month for cloud |
| CI/CD | 2000 minutes/month | $4/month for more |
| Browser Automation | Unlimited local | $25/month for cloud |

## 🚀 Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/your-org/orbit-agents
cd orbit-agents

# Start free development stack
docker-compose -f docker-compose.free.yml up -d

# Install dependencies
pip install -r requirements.txt
npm install

# Start services
make start-free-tier
```

## 💡 Cost Optimization Tips

1. **Use local development** for testing
2. **Implement caching** to reduce API calls
3. **Use CDN** for static assets (Cloudflare is free)
4. **Optimize Docker images** to reduce storage costs
5. **Use free SSL certificates** (Let's Encrypt)
6. **Monitor usage** with free tools (Prometheus/Grafana)

## 🔧 Environment Variables

```bash
# Free tier configuration
export NODE_ENV=production
export DATABASE_URL=sqlite:///./orbit.db
export SEARCH_ENGINE=opensearch
export STORAGE_TYPE=filesystem
export MONITORING_ENABLED=true
export AI_PROVIDER=ollama
export BROWSER_AUTOMATION=playwright
```
