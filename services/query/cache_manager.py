"""
Redis cache manager with comprehensive error handling, connection pooling,
and graceful degradation for the Query Service.
"""

import json
import hashlib
import logging
import time
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager
import asyncio

import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis cache manager with comprehensive error handling and fallback mechanisms.
    """
    
    def __init__(self):
        """Initialize the cache manager with connection pool."""
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
        self.is_connected = False
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        
        # Fallback in-memory cache for when Redis is unavailable
        self.fallback_cache: Dict[str, Dict[str, Any]] = {}
        self.fallback_max_size = 1000
        
        # Metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_errors = 0
        self.fallback_hits = 0
    
    async def initialize(self) -> bool:
        """Initialize Redis connection with retries."""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Create connection pool
                self.connection_pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    password=settings.REDIS_PASSWORD,
                    max_connections=20,
                    retry_on_timeout=True,
                    retry_on_error=[ConnectionError, TimeoutError],
                    health_check_interval=30,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    socket_keepalive_options={
                        1: 1,  # TCP_KEEPIDLE
                        2: 3,  # TCP_KEEPINTVL  
                        3: 5   # TCP_KEEPCNT
                    }
                )
                
                # Create Redis client
                self.redis_client = redis.Redis(
                    connection_pool=self.connection_pool,
                    decode_responses=True
                )
                
                # Test connection
                await self.redis_client.ping()
                self.is_connected = True
                self.last_health_check = time.time()
                
                logger.info("Successfully connected to Redis")
                return True
                
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        logger.error("Failed to connect to Redis after all attempts. Using fallback cache.")
        self.is_connected = False
        return False
    
    async def close(self):
        """Close Redis connections gracefully."""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        
        if self.connection_pool:
            try:
                await self.connection_pool.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting connection pool: {e}")
    
    async def health_check(self) -> bool:
        """Check Redis health and attempt reconnection if needed."""
        current_time = time.time()
        
        # Skip if we checked recently
        if current_time - self.last_health_check < self.health_check_interval:
            return self.is_connected
        
        self.last_health_check = current_time
        
        if not self.redis_client:
            return await self.initialize()
        
        try:
            await self.redis_client.ping()
            if not self.is_connected:
                logger.info("Redis connection restored")
                self.is_connected = True
            return True
        except Exception as e:
            if self.is_connected:
                logger.warning(f"Redis health check failed: {e}")
                self.is_connected = False
            return False
    
    def _generate_cache_key(self, query: str, prefix: str = "parse") -> str:
        """Generate a consistent cache key for a query."""
        # Normalize query for consistent caching
        normalized = query.lower().strip()
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        # Create hash
        query_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"query_service:{prefix}:{query_hash}"
    
    async def get_parsed_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached parsed query result.
        
        Args:
            query: The natural language query
            
        Returns:
            Cached parsed query data or None if not found
        """
        cache_key = self._generate_cache_key(query, "parse")
        
        # Try Redis first
        if await self.health_check():
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_hits += 1
                    logger.debug(f"Cache hit for query: {query[:50]}...")
                    return json.loads(cached_data)
                else:
                    self.cache_misses += 1
                    
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
                self.cache_errors += 1
                self.is_connected = False
        
        # Try fallback cache
        if cache_key in self.fallback_cache:
            entry = self.fallback_cache[cache_key]
            # Check expiration
            if time.time() < entry['expires_at']:
                self.fallback_hits += 1
                logger.debug(f"Fallback cache hit for query: {query[:50]}...")
                return entry['data']
            else:
                # Remove expired entry
                del self.fallback_cache[cache_key]
        
        return None
    
    async def set_parsed_query(self, query: str, parsed_data: Dict[str, Any]) -> bool:
        """
        Cache parsed query result.
        
        Args:
            query: The natural language query
            parsed_data: The parsed query data to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        cache_key = self._generate_cache_key(query, "parse")
        
        # Prepare data for caching
        cache_data = {
            'query': query,
            'parsed_data': parsed_data,
            'timestamp': time.time(),
            'version': '1.0'
        }
        
        # Try Redis first
        if await self.health_check():
            try:
                await self.redis_client.setex(
                    cache_key,
                    settings.CACHE_TTL,
                    json.dumps(cache_data, default=str)
                )
                logger.debug(f"Cached query result: {query[:50]}...")
                return True
                
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
                self.cache_errors += 1
                self.is_connected = False
        
        # Fallback to in-memory cache
        return self._set_fallback_cache(cache_key, cache_data)
    
    def _set_fallback_cache(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """Set data in fallback in-memory cache."""
        try:
            # Clean up if cache is full
            if len(self.fallback_cache) >= self.fallback_max_size:
                # Remove oldest entries (simple LRU)
                oldest_keys = sorted(
                    self.fallback_cache.keys(),
                    key=lambda k: self.fallback_cache[k].get('timestamp', 0)
                )[:100]
                for key in oldest_keys:
                    del self.fallback_cache[key]
            
            # Add new entry
            self.fallback_cache[cache_key] = {
                'data': data,
                'expires_at': time.time() + settings.CACHE_TTL,
                'timestamp': time.time()
            }
            
            logger.debug(f"Added to fallback cache: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Fallback cache error: {e}")
            return False
    
    async def get_search_results(self, search_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search results."""
        cache_key = self._generate_cache_key(search_key, "search")
        
        if await self.health_check():
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_hits += 1
                    return json.loads(cached_data)
                else:
                    self.cache_misses += 1
            except Exception as e:
                logger.warning(f"Redis get error for search: {e}")
                self.cache_errors += 1
        
        return None
    
    async def set_search_results(self, search_key: str, results: Dict[str, Any]) -> bool:
        """Cache search results with shorter TTL."""
        cache_key = self._generate_cache_key(search_key, "search")
        
        # Use shorter TTL for search results (30 minutes)
        search_ttl = min(settings.CACHE_TTL, 1800)
        
        if await self.health_check():
            try:
                await self.redis_client.setex(
                    cache_key,
                    search_ttl,
                    json.dumps(results, default=str)
                )
                return True
            except Exception as e:
                logger.warning(f"Redis set error for search: {e}")
                self.cache_errors += 1
        
        return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        if not await self.health_check():
            return 0
        
        try:
            # Get all matching keys
            keys = await self.redis_client.keys(f"query_service:{pattern}:*")
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'is_connected': self.is_connected,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_errors': self.cache_errors,
            'fallback_hits': self.fallback_hits,
            'fallback_cache_size': len(self.fallback_cache),
            'hit_rate': (
                self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0 else 0
            )
        }
        
        # Get Redis info if connected
        if await self.health_check():
            try:
                redis_info = await self.redis_client.info()
                stats.update({
                    'redis_memory_used': redis_info.get('used_memory_human', 'unknown'),
                    'redis_connected_clients': redis_info.get('connected_clients', 0),
                    'redis_total_commands': redis_info.get('total_commands_processed', 0),
                })
            except Exception as e:
                logger.warning(f"Failed to get Redis info: {e}")
        
        return stats
    
    async def clear_cache(self) -> bool:
        """Clear all cache entries (use with caution)."""
        success = False
        
        # Clear Redis cache
        if await self.health_check():
            try:
                keys = await self.redis_client.keys("query_service:*")
                if keys:
                    await self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} Redis cache entries")
                success = True
            except Exception as e:
                logger.error(f"Failed to clear Redis cache: {e}")
        
        # Clear fallback cache
        self.fallback_cache.clear()
        logger.info("Cleared fallback cache")
        
        return success


# Global cache manager instance
cache_manager = CacheManager() 