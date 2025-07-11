# OrbitAgents Development Guide

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+ and pip
- Git

### One-Command Setup
```bash
git clone <repository-url> && cd OrbitAgents
npm run setup
```

### Manual Setup
```bash
# 1. Install dependencies
npm run install-all

# 2. Set up Ollama (optional but recommended)
npm run setup:ollama

# 3. Run quick integration test
npm run test:quick

# 4. Start development environment
npm run dev
```

## 🏗️ Project Structure

```
OrbitAgents/
├── 📁 api/                     # Python backend
│   ├── enhanced_browser_agent.py    # Main AI agent
│   ├── cloudflare_integration.py    # Edge computing
│   ├── index.py                     # Flask API
│   └── requirements.txt             # Python dependencies
├── 📁 frontend/                # React frontend
│   ├── src/App.tsx                  # Main app component
│   ├── src/pages/Login.tsx          # Authentication
│   └── package.json                 # Node dependencies
├── 📁 tests/                   # Testing suite
│   ├── quick_integration_test.py    # Local dev validation
│   ├── e2e_validation_suite.py      # Comprehensive E2E
│   └── test_browser_agent_e2e.py    # Agent-specific tests
├── 📁 scripts/                # Automation scripts
│   ├── troubleshooting.sh           # Quick fixes
│   ├── setup-cloudflare.sh         # Edge deployment
│   └── deploy-workers.sh            # Workers deployment
├── 📁 monitoring/              # Observability
│   └── advanced_monitoring.py      # Metrics & health
├── 📁 workers/                 # Cloudflare Workers
│   ├── agent-state/                # Durable Objects
│   ├── ai-gateway/                  # AI caching
│   └── api-proxy/                   # CORS & routing
├── package.json                # Root configuration
├── setup.sh                   # Main setup script
└── README.md                   # This file
```

## 🧪 Testing Strategy

### Quick Integration Test
Validates local development environment:
```bash
npm run test:quick
```

### Comprehensive E2E Validation
Tests entire system including Cloudflare integration:
```bash
npm run test:e2e
```

### Browser Agent Tests
Specific tests for AI agent functionality:
```bash
npm run test:browser
```

## 🛠️ Development Workflows

### Daily Development
```bash
# Start development servers
npm run dev

# Check health status
npm run health

# Run quick tests
npm run test:quick
```

### Troubleshooting
```bash
# Automated troubleshooting
npm run troubleshoot

# Manual fixes
npm run troubleshoot --fix-deps    # Fix dependencies
npm run troubleshoot --check-ports # Check port conflicts
npm run troubleshoot --setup-ollama # Setup Ollama
```

### Monitoring
```bash
# Start monitoring dashboard
npm run monitor

# View at http://localhost:8000
```

## ☁️ Cloudflare Edge Deployment

### Setup
```bash
# Initialize Cloudflare Workers
npm run setup:cloudflare

# Configure credentials in .env.cloudflare
# Deploy to edge
npm run deploy:workers
```

### Environment Variables
Create `.env.cloudflare`:
```env
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_api_token
CLOUDFLARE_AI_GATEWAY_URL=https://gateway.ai.cloudflare.com/v1/your_account/your_gateway
```

## 🤖 AI Agent Features

### Core Capabilities
- **Vision-Capable Automation**: CV + OCR for UI element detection
- **Advanced Planning**: AutoGen + LangGraph orchestration
- **Long-term Memory**: ChromaDB vector storage
- **Policy Guardrails**: Security and content filtering
- **Self-Healing**: Automatic error recovery
- **Hybrid Inference**: Local Ollama + Cloudflare Workers AI

### Agent Architecture
```
┌──────── UI (React) ────────┐
│ Natural-lang prompt        │
└────┬────────┬──────────────┘
     │        │
     │   Event stream (WS)
     ▼        ▼
Planner LLM (Mixtral) ──► LangGraph DAG ──► Tool nodes
     ▲                         │
     │ Reflection              ▼
Memory (Durable Object + Chroma)     WebSurfer (Playwright)
```

### Usage Examples

#### Basic Navigation
```python
agent = EnhancedBrowserAgent()
await agent.execute_task("Navigate to example.com and take a screenshot")
```

#### Data Extraction
```python
result = await agent.execute_task(
    "Go to news.ycombinator.com and extract the top 5 story titles"
)
```

#### Form Interaction
```python
await agent.execute_task(
    "Fill out the contact form at example.com/contact with test data"
)
```

## 📊 Monitoring & Observability

### Built-in Monitoring
- **OpenTelemetry**: Distributed tracing
- **Prometheus**: Metrics collection
- **Health Checks**: System status monitoring
- **Performance Tracking**: Response times and resource usage

### Monitoring Dashboard
Access at http://localhost:8000 when running:
```bash
npm run monitor
```

### Key Metrics
- Agent task success rate
- Browser automation performance
- Memory usage and vector search performance
- API response times
- Error rates and types

## 🔒 Security & Privacy

### Policy Framework
- Content filtering and malicious code detection
- Privacy-preserving data handling
- Secure credential management
- Rate limiting and abuse prevention

### Security Features
- XSS and injection attack prevention
- Safe browsing environment isolation
- Encrypted state storage
- Audit logging and compliance

## 🚀 Performance Optimization

### Local Performance
- **Ollama Integration**: Run LLMs locally for speed
- **Browser Reuse**: Persistent browser contexts
- **Memory Management**: Efficient vector storage
- **Caching**: Intelligent response caching

### Edge Performance
- **AI Gateway**: Automatic response caching
- **Durable Objects**: Zero-latency state storage
- **Global Distribution**: Edge-deployed Workers
- **Smart Routing**: Optimal inference backend selection

## 🔧 Advanced Configuration

### Ollama Models
```bash
# Install recommended models
ollama pull mixtral:8x22b     # Large reasoning model
ollama pull phi3:mini         # Fast lightweight model
ollama pull llama3.1:8b       # Balanced model
```

### Environment Configuration
```env
# Development
NODE_ENV=development
FLASK_ENV=development
PYTHONPATH=./api

# AI Configuration
OPENAI_API_KEY=sk-...         # Optional fallback
OLLAMA_BASE_URL=http://localhost:11434

# Cloudflare (Production)
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
USE_CLOUDFLARE_AI=true
USE_DURABLE_OBJECTS=true
```

## 📝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Run `npm run setup` to initialize
4. Make changes and test with `npm run test:quick`
5. Submit a pull request

### Code Quality
- **Linting**: ESLint for TypeScript, Black for Python
- **Type Safety**: Full TypeScript and Python type hints
- **Testing**: Comprehensive test coverage
- **Documentation**: Inline docs and examples

### Architecture Decisions
- **AutoGen + LangGraph**: Multi-agent orchestration
- **Playwright**: Cross-browser automation
- **ChromaDB**: Vector memory storage
- **Cloudflare Workers**: Edge computing
- **OpenTelemetry**: Observability standard

## 🐛 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
npm run troubleshoot --check-ports
```

#### Dependency Issues
```bash
npm run troubleshoot --fix-deps
```

#### Ollama Not Working
```bash
npm run troubleshoot --setup-ollama
```

#### Browser Issues
```bash
# Reinstall Playwright browsers
cd api && playwright install
```

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=true
export LOG_LEVEL=debug
npm run dev
```

### Performance Issues
```bash
# Check resource usage
npm run monitor

# Run performance tests
npm run test:e2e
```

## 📚 Resources

### Documentation
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [LangGraph Guide](https://langchain-ai.github.io/langgraph/)
- [Playwright API](https://playwright.dev/python/)
- [Cloudflare Workers](https://developers.cloudflare.com/workers/)

### Community
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Architecture and usage questions
- **Discord**: Real-time community support

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- ✅ Basic browser automation
- ✅ AI agent integration
- ✅ Local development environment
- ✅ Monitoring and observability

### Phase 2: Enhancement
- ⏳ Advanced vision capabilities
- ⏳ Cloudflare edge deployment
- ⏳ Multi-site orchestration
- ⏳ Continuous learning

### Phase 3: Scale
- 📋 Enterprise features
- 📋 Marketplace integration
- 📋 Advanced security
- 📋 Performance optimization

---

## 🎯 Quick Commands Reference

```bash
# Setup and Development
npm run setup                    # Complete environment setup
npm run dev                      # Start development servers
npm run test:quick              # Quick integration test

# Testing
npm run test:e2e                # Full E2E validation
npm run test:browser            # Browser agent tests

# Operations
npm run troubleshoot            # Automated troubleshooting
npm run monitor                 # Start monitoring dashboard
npm run health                  # Check system health

# Deployment
npm run setup:cloudflare        # Setup Cloudflare Workers
npm run deploy:workers          # Deploy to edge
```

---

*OrbitAgents - Building the future of AI-powered web automation* 🚀
