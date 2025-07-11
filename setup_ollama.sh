#!/bin/bash

# Ollama Setup and Integration Script for Enhanced Browser Agent
# This script sets up Ollama with the required models for local AI inference

set -e

echo "🚀 Setting up Ollama for Enhanced Browser Agent..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    
    # Install Ollama on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    else
        # Install on Linux
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
else
    echo "✅ Ollama already installed"
fi

# Start Ollama service
echo "🔧 Starting Ollama service..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # On macOS, start as background service
    if ! pgrep -f "ollama serve" > /dev/null; then
        nohup ollama serve > /dev/null 2>&1 &
        sleep 3
    fi
else
    # On Linux, use systemctl if available
    if command -v systemctl &> /dev/null; then
        sudo systemctl start ollama
        sudo systemctl enable ollama
    else
        nohup ollama serve > /dev/null 2>&1 &
        sleep 3
    fi
fi

# Function to pull model with retry
pull_model() {
    local model=$1
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "📥 Pulling $model (attempt $attempt/$max_attempts)..."
        if ollama pull "$model"; then
            echo "✅ Successfully pulled $model"
            return 0
        else
            echo "❌ Failed to pull $model (attempt $attempt)"
            attempt=$((attempt + 1))
            if [ $attempt -le $max_attempts ]; then
                echo "⏳ Waiting 10 seconds before retry..."
                sleep 10
            fi
        fi
    done
    
    echo "❌ Failed to pull $model after $max_attempts attempts"
    return 1
}

# Pull required models
echo "📥 Pulling AI models for browser agent..."

# Core models for different use cases
models=(
    "phi3:mini"          # Fast, small model for quick tasks
    "llama3.2:3b"       # Balanced model for general tasks
    "qwen2.5:7b"        # Larger model for complex reasoning
    "nomic-embed-text"   # Embedding model for memory/search
)

# Try to pull each model
failed_models=()
for model in "${models[@]}"; do
    if ! pull_model "$model"; then
        failed_models+=("$model")
    fi
done

# Alternative fallback models if main ones fail
if [ ${#failed_models[@]} -gt 0 ]; then
    echo "⚠️  Some models failed to download. Trying alternatives..."
    
    # Try smaller/alternative models
    fallback_models=(
        "tinyllama"
        "orca-mini"
        "phi3:mini"
    )
    
    for model in "${fallback_models[@]}"; do
        if pull_model "$model"; then
            echo "✅ Successfully pulled fallback model: $model"
            break
        fi
    done
fi

# Verify Ollama is working
echo "🔍 Verifying Ollama installation..."
if ollama list > /dev/null 2>&1; then
    echo "✅ Ollama is working correctly"
    echo "📋 Available models:"
    ollama list
else
    echo "❌ Ollama verification failed"
    exit 1
fi

# Test a simple generation
echo "🧪 Testing model generation..."
if ollama generate --model phi3:mini --prompt "Hello, respond with just 'OK'" | grep -q "OK"; then
    echo "✅ Model generation test passed"
else
    echo "⚠️  Model generation test failed, but installation seems complete"
fi

# Create Ollama configuration
echo "⚙️  Creating Ollama configuration..."
mkdir -p ~/.config/ollama

cat > ~/.config/ollama/config.json << EOF
{
    "host": "0.0.0.0:11434",
    "origins": ["*"],
    "models_path": "~/.ollama/models",
    "keep_alive": "5m",
    "parallel_requests": 4,
    "gpu_memory_utilization": 0.9,
    "cpu_threads": 0
}
EOF

# Create a simple health check script
cat > check_ollama.sh << 'EOF'
#!/bin/bash
# Health check script for Ollama

echo "🔍 Checking Ollama health..."

# Check if service is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "❌ Ollama service not running"
    echo "Starting Ollama..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Check if API is responding
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama API is responding"
    
    # List available models
    echo "📋 Available models:"
    curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "Unable to parse models"
else
    echo "❌ Ollama API not responding"
    exit 1
fi

# Test generation
echo "🧪 Testing generation..."
response=$(curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{"model":"phi3:mini","prompt":"Say OK","stream":false}' | \
    jq -r '.response' 2>/dev/null)

if [[ -n "$response" && "$response" != "null" ]]; then
    echo "✅ Generation test passed: $response"
else
    echo "⚠️  Generation test failed"
fi
EOF

chmod +x check_ollama.sh

# Create model benchmarking script
cat > benchmark_models.py << 'EOF'
#!/usr/bin/env python3
"""
Benchmark script for Ollama models performance
"""

import asyncio
import aiohttp
import time
import json
from typing import List, Dict

async def test_model_performance(model: str, prompt: str) -> Dict:
    """Test a model's performance"""
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            async with session.post("http://localhost:11434/api/generate", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()
                    
                    return {
                        "model": model,
                        "success": True,
                        "response_time": end_time - start_time,
                        "response_length": len(result.get("response", "")),
                        "tokens_per_second": result.get("eval_count", 0) / (result.get("eval_duration", 1) / 1e9)
                    }
                else:
                    return {
                        "model": model,
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
                    
    except Exception as e:
        return {
            "model": model,
            "success": False,
            "error": str(e)
        }

async def benchmark_models():
    """Benchmark all available models"""
    # Test prompt
    prompt = "Explain what a web browser is in one sentence."
    
    # Get available models
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    models = [model["name"] for model in models_data.get("models", [])]
                else:
                    models = ["phi3:mini", "llama3.2:3b", "qwen2.5:7b"]
    except:
        models = ["phi3:mini"]
    
    print(f"🧪 Benchmarking {len(models)} models...")
    
    results = []
    for model in models:
        print(f"Testing {model}...")
        result = await test_model_performance(model, prompt)
        results.append(result)
        
        if result["success"]:
            print(f"✅ {model}: {result['response_time']:.2f}s, {result['tokens_per_second']:.1f} tokens/s")
        else:
            print(f"❌ {model}: {result['error']}")
    
    # Save results
    with open("model_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📊 Benchmark complete! Results saved to model_benchmark_results.json")
    
    # Find best performing model
    successful_results = [r for r in results if r["success"]]
    if successful_results:
        fastest = min(successful_results, key=lambda x: x["response_time"])
        print(f"🏆 Fastest model: {fastest['model']} ({fastest['response_time']:.2f}s)")

if __name__ == "__main__":
    asyncio.run(benchmark_models())
EOF

chmod +x benchmark_models.py

echo ""
echo "🎉 Ollama setup complete!"
echo ""
echo "📚 Available commands:"
echo "  ./check_ollama.sh      - Check Ollama health and test generation"
echo "  ./benchmark_models.py  - Benchmark model performance"
echo "  ollama list            - List installed models"
echo "  ollama serve           - Start Ollama server manually"
echo ""
echo "🔧 Configuration:"
echo "  API URL: http://localhost:11434"
echo "  Config: ~/.config/ollama/config.json"
echo "  Models: ~/.ollama/models"
echo ""
echo "🚀 Your Enhanced Browser Agent is now ready to use local AI!"
echo "   Try running: python tests/test_browser_agent_e2e.py"
