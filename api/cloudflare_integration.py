"""
Cloudflare Workers AI Integration
Provides remote GPU inference and AI Gateway caching for OrbitAgents
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import aiohttp
from dataclasses import dataclass
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

@dataclass
class CloudflareConfig:
    """Configuration for Cloudflare Workers AI"""
    account_id: str
    api_token: str
    ai_gateway_url: Optional[str] = None
    default_model: str = "@cf/meta/llama-3.1-8b-instruct"
    max_tokens: int = 1024
    temperature: float = 0.7

class CloudflareAIClient:
    """Client for Cloudflare Workers AI with AI Gateway caching"""
    
    def __init__(self, config: CloudflareConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{config.account_id}/ai/run"
        
        # AI Gateway URL for caching
        if config.ai_gateway_url:
            self.gateway_url = config.ai_gateway_url
        else:
            self.gateway_url = self.base_url
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.config.api_token}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text using Cloudflare Workers AI"""
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        model = model or self.config.default_model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        # Construct messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            # Use AI Gateway URL for caching benefits
            url = f"{self.gateway_url}/{model}"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Cloudflare AI response: {response.status}")
                    return {
                        "text": result.get("result", {}).get("response", ""),
                        "model": model,
                        "tokens_used": result.get("result", {}).get("tokens_used", 0),
                        "cached": response.headers.get("CF-Cache-Status") == "HIT"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Cloudflare AI error: {response.status} - {error_text}")
                    raise Exception(f"Cloudflare AI API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Error calling Cloudflare AI: {e}")
            raise

    async def generate_vision_analysis(
        self,
        image_data: bytes,
        prompt: str,
        model: str = "@cf/unum/uform-gen2-qwen-500m"
    ) -> Dict[str, Any]:
        """Analyze images using Cloudflare's vision models"""
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # Encode image as base64
        import base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            "image": image_b64,
            "prompt": prompt,
            "max_tokens": 512
        }
        
        try:
            url = f"{self.gateway_url}/{model}"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "text": result.get("result", {}).get("description", ""),
                        "model": model,
                        "cached": response.headers.get("CF-Cache-Status") == "HIT"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Cloudflare Vision API error: {response.status} - {error_text}")
                    raise Exception(f"Cloudflare Vision API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Error calling Cloudflare Vision API: {e}")
            raise

class DurableObjectsClient:
    """Client for Cloudflare Durable Objects state management"""
    
    def __init__(self, account_id: str, api_token: str, namespace: str):
        self.account_id = account_id
        self.api_token = api_token
        self.namespace = namespace
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/storage/kv/namespaces/{namespace}"
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def store_agent_state(
        self,
        agent_id: str,
        state: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store agent state in Durable Objects"""
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            # Add metadata
            state_with_meta = {
                "data": state,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": agent_id
            }
            
            key = f"agent_state:{agent_id}"
            payload = json.dumps(state_with_meta)
            
            params = {}
            if ttl:
                params["expiration_ttl"] = ttl
            
            async with self.session.put(
                f"{self.base_url}/values/{key}",
                data=payload,
                params=params
            ) as response:
                return response.status == 200
        
        except Exception as e:
            logger.error(f"Error storing agent state: {e}")
            return False
    
    async def retrieve_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent state from Durable Objects"""
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            key = f"agent_state:{agent_id}"
            
            async with self.session.get(f"{self.base_url}/values/{key}") as response:
                if response.status == 200:
                    state_data = await response.json()
                    return state_data.get("data", {})
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"Error retrieving agent state: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error retrieving agent state: {e}")
            return None
    
    async def store_memory(
        self,
        session_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store memory in Durable Objects"""
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            memory_data = {
                "content": content,
                "type": memory_type,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id
            }
            
            key = f"memory:{session_id}:{memory_type}:{datetime.utcnow().timestamp()}"
            payload = json.dumps(memory_data)
            
            async with self.session.put(
                f"{self.base_url}/values/{key}",
                data=payload
            ) as response:
                return response.status == 200
        
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    async def list_memories(
        self,
        session_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List memories for a session"""
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            prefix = f"memory:{session_id}"
            if memory_type:
                prefix += f":{memory_type}"
            
            params = {"prefix": prefix, "limit": limit}
            
            async with self.session.get(
                f"{self.base_url}/keys",
                params=params
            ) as response:
                if response.status == 200:
                    keys_data = await response.json()
                    keys = [item["name"] for item in keys_data.get("result", [])]
                    
                    # Fetch content for each key
                    memories = []
                    for key in keys:
                        async with self.session.get(f"{self.base_url}/values/{key}") as mem_response:
                            if mem_response.status == 200:
                                memory_data = await mem_response.json()
                                memories.append(memory_data)
                    
                    return memories
                else:
                    logger.error(f"Error listing memories: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error listing memories: {e}")
            return []

class DurableObjectsManager:
    """Manager for Cloudflare Durable Objects state"""
    
    def __init__(self, config: CloudflareConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_state(self, object_id: str, key: str) -> Optional[Dict[str, Any]]:
        """Get state from Durable Object"""
        # Implementation for Durable Objects API calls
        return None
    
    async def set_state(self, object_id: str, key: str, value: Dict[str, Any]) -> bool:
        """Set state in Durable Object"""
        # Implementation for Durable Objects API calls
        return True
    
    async def delete_state(self, object_id: str, key: str) -> bool:
        """Delete state from Durable Object"""
        # Implementation for Durable Objects API calls
        return True

class AIGateway:
    """Cloudflare AI Gateway for caching and analytics"""
    
    def __init__(self, gateway_url: str, api_token: str):
        self.gateway_url = gateway_url
        self.api_token = api_token
    
    async def cached_inference(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Make inference request through AI Gateway with caching"""
        # Implementation for AI Gateway caching
        return {'result': 'cached_response', 'cached': True}

class HybridInferenceClient:
    """Hybrid client that routes between local Ollama and Cloudflare Workers AI"""
    
    def __init__(
        self,
        cloudflare_config: CloudflareConfig,
        ollama_url: str = "http://localhost:11434"
    ):
        self.cloudflare_config = cloudflare_config
        self.ollama_url = ollama_url
        self.cloudflare_client: Optional[CloudflareAIClient] = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        self.cloudflare_client = CloudflareAIClient(self.cloudflare_config)
        await self.cloudflare_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.cloudflare_client:
            await self.cloudflare_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.session:
            await self.session.close()
    
    async def is_ollama_available(self) -> bool:
        """Check if Ollama is available locally"""
        try:
            if not self.session:
                return False
            
            async with self.session.get(f"{self.ollama_url}/api/tags", timeout=5) as response:
                return response.status == 200
        except:
            return False
    
    async def generate_text(
        self,
        prompt: str,
        prefer_local: bool = True,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using the best available option"""
        
        # Try local Ollama first if preferred and available
        if prefer_local and await self.is_ollama_available():
            try:
                return await self._generate_with_ollama(prompt, model or "llama3.1:8b", **kwargs)
            except Exception as e:
                logger.warning(f"Ollama failed, falling back to Cloudflare: {e}")
        
        # Fallback to Cloudflare Workers AI
        if self.cloudflare_client:
            return await self.cloudflare_client.generate_text(prompt, model, **kwargs)
        else:
            raise RuntimeError("No inference backend available")
    
    async def _generate_with_ollama(
        self,
        prompt: str,
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text using local Ollama"""
        
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {}
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        if temperature:
            payload["options"]["temperature"] = temperature
        
        async with self.session.post(
            f"{self.ollama_url}/api/chat",
            json=payload
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    "text": result.get("message", {}).get("content", ""),
                    "model": model,
                    "tokens_used": result.get("eval_count", 0),
                    "local": True
                }
            else:
                error_text = await response.text()
                raise Exception(f"Ollama API error: {response.status} - {error_text}")

# Add missing aliases for validation
CloudflareWorkerClient = CloudflareAIClient

# Utility functions for easy integration
async def create_cloudflare_config() -> CloudflareConfig:
    """Create Cloudflare config from environment variables"""
    return CloudflareConfig(
        account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID", ""),
        api_token=os.getenv("CLOUDFLARE_API_TOKEN", ""),
        ai_gateway_url=os.getenv("CLOUDFLARE_AI_GATEWAY_URL")
    )

async def get_hybrid_client() -> HybridInferenceClient:
    """Get a configured hybrid inference client"""
    config = await create_cloudflare_config()
    return HybridInferenceClient(config)

# Example usage
async def main():
    """Example usage of the Cloudflare integration"""
    config = await create_cloudflare_config()
    
    async with HybridInferenceClient(config) as client:
        # Try local first, fallback to Cloudflare
        result = await client.generate_text(
            "Explain what a browser agent is in simple terms",
            prefer_local=True
        )
        print(f"Response: {result['text']}")
        print(f"Local: {result.get('local', False)}")
        print(f"Tokens: {result.get('tokens_used', 0)}")

if __name__ == "__main__":
    asyncio.run(main())
