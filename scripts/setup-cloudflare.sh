#!/bin/bash

# Cloudflare Workers and Edge Setup Script
# Sets up Cloudflare Workers AI, AI Gateway, and Durable Objects for OrbitAgents

set -euo pipefail

echo "🌍 Setting up Cloudflare Edge Infrastructure for OrbitAgents"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in the right directory
if [[ ! -f "package.json" ]]; then
    log_error "Please run this script from the OrbitAgents project root"
    exit 1
fi

# Check for required tools
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v npm &> /dev/null; then
        log_error "npm not found. Please install Node.js from https://nodejs.org/"
        exit 1
    fi
    
    if ! command -v npx &> /dev/null; then
        log_error "npx not found. Please install Node.js from https://nodejs.org/"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Install Wrangler CLI
install_wrangler() {
    log_info "Installing Wrangler CLI..."
    
    if ! command -v wrangler &> /dev/null; then
        npm install -g @cloudflare/wrangler
        log_success "Wrangler CLI installed"
    else
        log_success "Wrangler CLI already available"
    fi
}

# Create Cloudflare Workers project structure
setup_workers_project() {
    log_info "Setting up Cloudflare Workers project structure..."
    
    # Create workers directory
    mkdir -p workers/agent-state
    mkdir -p workers/ai-gateway
    mkdir -p workers/api-proxy
    
    # Create Durable Objects for agent state
    cat > workers/agent-state/wrangler.toml << EOF
name = "orbit-agent-state"
main = "src/index.js"
compatibility_date = "2024-01-01"

[[durable_objects.bindings]]
name = "AGENT_STATE"
class_name = "AgentState"

[[migrations]]
tag = "v1"
new_classes = ["AgentState"]

[env.production]
name = "orbit-agent-state-prod"

[env.staging]
name = "orbit-agent-state-staging"
EOF

    # Create Durable Object implementation
    mkdir -p workers/agent-state/src
    cat > workers/agent-state/src/index.js << 'EOF'
/**
 * Durable Object for managing agent state and memory
 */
export class AgentState {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }

  async fetch(request) {
    const url = new URL(request.url);
    const agentId = url.searchParams.get('agentId');
    
    if (!agentId) {
      return new Response('Missing agentId parameter', { status: 400 });
    }

    switch (request.method) {
      case 'GET':
        return this.getState(agentId);
      case 'PUT':
        return this.setState(agentId, request);
      case 'POST':
        return this.appendMemory(agentId, request);
      case 'DELETE':
        return this.clearState(agentId);
      default:
        return new Response('Method not allowed', { status: 405 });
    }
  }

  async getState(agentId) {
    try {
      const state = await this.state.storage.get(`state:${agentId}`);
      const memories = await this.state.storage.list({ prefix: `memory:${agentId}:` });
      
      const memoryArray = [];
      for (const [key, value] of memories) {
        memoryArray.push(value);
      }
      
      return new Response(JSON.stringify({
        state: state || {},
        memories: memoryArray,
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      return new Response(`Error retrieving state: ${error.message}`, { status: 500 });
    }
  }

  async setState(agentId, request) {
    try {
      const newState = await request.json();
      await this.state.storage.put(`state:${agentId}`, {
        ...newState,
        lastUpdated: new Date().toISOString()
      });
      
      return new Response('State updated successfully', { status: 200 });
    } catch (error) {
      return new Response(`Error updating state: ${error.message}`, { status: 500 });
    }
  }

  async appendMemory(agentId, request) {
    try {
      const memory = await request.json();
      const memoryId = `memory:${agentId}:${Date.now()}:${Math.random().toString(36).substr(2, 9)}`;
      
      await this.state.storage.put(memoryId, {
        ...memory,
        timestamp: new Date().toISOString(),
        agentId
      });
      
      return new Response(JSON.stringify({ memoryId }), {
        headers: { 'Content-Type': 'application/json' },
        status: 201
      });
    } catch (error) {
      return new Response(`Error storing memory: ${error.message}`, { status: 500 });
    }
  }

  async clearState(agentId) {
    try {
      // Clear main state
      await this.state.storage.delete(`state:${agentId}`);
      
      // Clear memories
      const memories = await this.state.storage.list({ prefix: `memory:${agentId}:` });
      const deletePromises = [];
      for (const [key] of memories) {
        deletePromises.push(this.state.storage.delete(key));
      }
      await Promise.all(deletePromises);
      
      return new Response('State cleared successfully', { status: 200 });
    } catch (error) {
      return new Response(`Error clearing state: ${error.message}`, { status: 500 });
    }
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const agentId = url.searchParams.get('agentId');
    
    if (!agentId) {
      return new Response('Missing agentId parameter', { status: 400 });
    }
    
    // Get the Durable Object for this agent
    const id = env.AGENT_STATE.idFromName(agentId);
    const obj = env.AGENT_STATE.get(id);
    
    // Forward the request to the Durable Object
    return obj.fetch(request);
  }
};
EOF

    # Create AI Gateway proxy
    cat > workers/ai-gateway/wrangler.toml << EOF
name = "orbit-ai-gateway"
main = "src/index.js"
compatibility_date = "2024-01-01"

[vars]
AI_GATEWAY_ACCOUNT_TAG = "your-account-tag"
AI_GATEWAY_TOKEN = "your-gateway-token"

[env.production]
name = "orbit-ai-gateway-prod"

[env.staging]
name = "orbit-ai-gateway-staging"
EOF

    mkdir -p workers/ai-gateway/src
    cat > workers/ai-gateway/src/index.js << 'EOF'
/**
 * AI Gateway for caching and routing LLM requests
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Extract model and endpoint information
    const pathname = url.pathname;
    const isAIRequest = pathname.startsWith('/v1/') || pathname.includes('ai/run');
    
    if (!isAIRequest) {
      return new Response('Not Found', { status: 404 });
    }

    // Add AI Gateway headers for caching
    const headers = new Headers(request.headers);
    headers.set('CF-AI-Gateway', env.AI_GATEWAY_ACCOUNT_TAG);
    headers.set('Authorization', `Bearer ${env.AI_GATEWAY_TOKEN}`);
    
    // Create cache key based on request content
    const cacheKey = await this.generateCacheKey(request);
    const cache = caches.default;
    
    // Check cache first
    let response = await cache.match(cacheKey);
    if (response) {
      // Add cache hit header
      response = new Response(response.body, response);
      response.headers.set('CF-Cache-Status', 'HIT');
      response.headers.set('CF-OrbitAgents-Cache', 'true');
      return response;
    }
    
    // Forward to upstream AI service
    const upstreamResponse = await this.forwardToUpstream(request, headers);
    
    // Cache successful responses
    if (upstreamResponse.status === 200) {
      const responseToCache = upstreamResponse.clone();
      ctx.waitUntil(cache.put(cacheKey, responseToCache));
    }
    
    // Add cache miss header
    upstreamResponse.headers.set('CF-Cache-Status', 'MISS');
    return upstreamResponse;
  },

  async generateCacheKey(request) {
    const url = new URL(request.url);
    const body = request.method === 'POST' ? await request.text() : '';
    
    // Create a hash of the request for caching
    const encoder = new TextEncoder();
    const data = encoder.encode(url.pathname + url.search + body);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    return `https://ai-cache.orbitagents.com/${hashHex}`;
  },

  async forwardToUpstream(request, headers) {
    const url = new URL(request.url);
    
    // Determine upstream URL based on the request
    let upstreamUrl;
    if (url.pathname.includes('openai')) {
      upstreamUrl = 'https://api.openai.com' + url.pathname;
    } else if (url.pathname.includes('anthropic')) {
      upstreamUrl = 'https://api.anthropic.com' + url.pathname;
    } else {
      // Default to Cloudflare Workers AI
      upstreamUrl = 'https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/ai/run' + url.pathname.replace('/v1', '');
    }
    
    const modifiedRequest = new Request(upstreamUrl, {
      method: request.method,
      headers: headers,
      body: request.body
    });
    
    return fetch(modifiedRequest);
  }
};
EOF

    # Create main API proxy
    cat > workers/api-proxy/wrangler.toml << EOF
name = "orbit-api-proxy"
main = "src/index.js"
compatibility_date = "2024-01-01"

[[durable_objects.bindings]]
name = "AGENT_STATE"
class_name = "AgentState"
script_name = "orbit-agent-state"

[vars]
BACKEND_URL = "https://your-backend.herokuapp.com"
ALLOWED_ORIGINS = "https://orbitagents.pages.dev,http://localhost:3000"

[env.production]
name = "orbit-api-proxy-prod"
vars = { BACKEND_URL = "https://your-production-backend.com" }

[env.staging]
name = "orbit-api-proxy-staging"
vars = { BACKEND_URL = "https://your-staging-backend.com" }
EOF

    mkdir -p workers/api-proxy/src
    cat > workers/api-proxy/src/index.js << 'EOF'
/**
 * Main API proxy with CORS and request routing
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return this.handleCORS(request, env);
    }
    
    // Route requests
    if (url.pathname.startsWith('/api/agent-state')) {
      return this.handleAgentState(request, env);
    } else if (url.pathname.startsWith('/api/ai')) {
      return this.handleAIRequest(request, env);
    } else {
      return this.proxyToBackend(request, env);
    }
  },

  handleCORS(request, env) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': this.getAllowedOrigin(request, env),
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    };
    
    return new Response(null, { headers: corsHeaders });
  },

  getAllowedOrigin(request, env) {
    const origin = request.headers.get('Origin');
    const allowedOrigins = env.ALLOWED_ORIGINS.split(',');
    
    if (allowedOrigins.includes(origin)) {
      return origin;
    }
    
    return allowedOrigins[0]; // Default to first allowed origin
  },

  async handleAgentState(request, env) {
    // Forward to Durable Objects
    const url = new URL(request.url);
    const agentId = url.searchParams.get('agentId');
    
    if (!agentId) {
      return new Response('Missing agentId parameter', { status: 400 });
    }
    
    const id = env.AGENT_STATE.idFromName(agentId);
    const obj = env.AGENT_STATE.get(id);
    
    const response = await obj.fetch(request);
    
    // Add CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': this.getAllowedOrigin(request, env),
      'Access-Control-Allow-Credentials': 'true',
    };
    
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders, ...Object.fromEntries(response.headers) }
    });
  },

  async handleAIRequest(request, env) {
    // Forward to AI Gateway
    const aiGatewayUrl = 'https://orbit-ai-gateway.your-workers.dev' + request.url.substring(request.url.indexOf('/api/ai') + 7);
    
    const modifiedRequest = new Request(aiGatewayUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });
    
    const response = await fetch(modifiedRequest);
    
    // Add CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': this.getAllowedOrigin(request, env),
      'Access-Control-Allow-Credentials': 'true',
    };
    
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders, ...Object.fromEntries(response.headers) }
    });
  },

  async proxyToBackend(request, env) {
    // Forward other requests to main backend
    const backendUrl = env.BACKEND_URL + request.url.substring(request.url.indexOf('/', 8));
    
    const modifiedRequest = new Request(backendUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });
    
    const response = await fetch(modifiedRequest);
    
    // Add CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': this.getAllowedOrigin(request, env),
      'Access-Control-Allow-Credentials': 'true',
    };
    
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders, ...Object.fromEntries(response.headers) }
    });
  }
};
EOF

    log_success "Cloudflare Workers project structure created"
}

# Create deployment scripts
create_deployment_scripts() {
    log_info "Creating deployment scripts..."
    
    cat > scripts/deploy-workers.sh << 'EOF'
#!/bin/bash

# Deploy all Cloudflare Workers
set -euo pipefail

echo "🚀 Deploying Cloudflare Workers for OrbitAgents"

# Check if Wrangler is logged in
if ! wrangler whoami > /dev/null 2>&1; then
    echo "Please log in to Cloudflare first:"
    echo "wrangler login"
    exit 1
fi

# Deploy Agent State Durable Object
echo "Deploying Agent State Durable Object..."
cd workers/agent-state
wrangler deploy --env staging
cd ../..

# Deploy AI Gateway
echo "Deploying AI Gateway..."
cd workers/ai-gateway
wrangler deploy --env staging
cd ../..

# Deploy API Proxy
echo "Deploying API Proxy..."
cd workers/api-proxy
wrangler deploy --env staging
cd ../..

echo "✅ All Workers deployed successfully!"
echo "Update your environment variables with the new Worker URLs."
EOF

    chmod +x scripts/deploy-workers.sh
    
    cat > scripts/test-workers.sh << 'EOF'
#!/bin/bash

# Test Cloudflare Workers deployment
set -euo pipefail

echo "🧪 Testing Cloudflare Workers deployment"

AGENT_STATE_URL="https://orbit-agent-state-staging.your-workers.dev"
AI_GATEWAY_URL="https://orbit-ai-gateway-staging.your-workers.dev"
API_PROXY_URL="https://orbit-api-proxy-staging.your-workers.dev"

# Test Agent State
echo "Testing Agent State Durable Object..."
curl -X PUT "$AGENT_STATE_URL?agentId=test-agent" \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'

curl -X GET "$AGENT_STATE_URL?agentId=test-agent"

# Test AI Gateway
echo "Testing AI Gateway..."
curl -X POST "$AI_GATEWAY_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'

# Test API Proxy
echo "Testing API Proxy..."
curl -X GET "$API_PROXY_URL/health"

echo "✅ All tests completed!"
EOF

    chmod +x scripts/test-workers.sh
    
    log_success "Deployment scripts created"
}

# Create environment configuration
create_environment_config() {
    log_info "Creating environment configuration..."
    
    # Add Cloudflare environment variables to .env files
    if [[ ! -f ".env.cloudflare" ]]; then
        cat > .env.cloudflare << EOF
# Cloudflare Configuration
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
CLOUDFLARE_API_TOKEN=your_api_token_here
CLOUDFLARE_ZONE_ID=your_zone_id_here

# AI Gateway
CLOUDFLARE_AI_GATEWAY_URL=https://gateway.ai.cloudflare.com/v1/your_account/your_gateway
CLOUDFLARE_AI_GATEWAY_TOKEN=your_gateway_token_here

# Workers URLs (update after deployment)
AGENT_STATE_WORKER_URL=https://orbit-agent-state.your-workers.dev
AI_GATEWAY_WORKER_URL=https://orbit-ai-gateway.your-workers.dev
API_PROXY_WORKER_URL=https://orbit-api-proxy.your-workers.dev

# Production URLs
PRODUCTION_AGENT_STATE_URL=https://orbit-agent-state-prod.your-workers.dev
PRODUCTION_AI_GATEWAY_URL=https://orbit-ai-gateway-prod.your-workers.dev
PRODUCTION_API_PROXY_URL=https://orbit-api-proxy-prod.your-workers.dev
EOF
        log_success "Created .env.cloudflare template"
    fi
    
    # Update API environment
    if [[ ! -f "api/.env.workers" ]]; then
        cat > api/.env.workers << EOF
# Cloudflare Workers Integration
CLOUDFLARE_ACCOUNT_ID=\${CLOUDFLARE_ACCOUNT_ID}
CLOUDFLARE_API_TOKEN=\${CLOUDFLARE_API_TOKEN}
CLOUDFLARE_AI_GATEWAY_URL=\${CLOUDFLARE_AI_GATEWAY_URL}

# Workers URLs
AGENT_STATE_WORKER_URL=\${AGENT_STATE_WORKER_URL}
AI_GATEWAY_WORKER_URL=\${AI_GATEWAY_WORKER_URL}

# Feature flags
USE_CLOUDFLARE_AI=true
USE_DURABLE_OBJECTS=true
USE_AI_GATEWAY_CACHE=true
EOF
        log_success "Created API Workers environment config"
    fi
}

# Main setup function
main() {
    log_info "Starting Cloudflare Edge setup..."
    
    check_dependencies
    install_wrangler
    setup_workers_project
    create_deployment_scripts
    create_environment_config
    
    log_success "Cloudflare Edge setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Sign up for Cloudflare and get your account ID and API token"
    echo "2. Update .env.cloudflare with your actual credentials"
    echo "3. Run 'wrangler login' to authenticate"
    echo "4. Run './scripts/deploy-workers.sh' to deploy the Workers"
    echo "5. Update your environment with the deployed Worker URLs"
    echo "6. Run './scripts/test-workers.sh' to verify deployment"
    echo ""
    echo "Documentation: https://developers.cloudflare.com/workers/"
}

# Run main function
main "$@"
