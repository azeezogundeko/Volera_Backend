import asyncio
import json
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta

class CacheManager:
    """
    A flexible, async-friendly cache management system with multiple backends.
    
    Supports:
    - In-memory caching
    - Redis caching (optional)
    - Configurable expiration
    - Thread-safe operations
    - Serialization/Deserialization
    """
    
    def __init__(
        self, 
        backend: str = 'memory', 
        max_size: int = 1000, 
        default_ttl: int = 3600
    ):
        """
        Initialize the cache manager.
        
        Args:
            backend (str): Cache backend type ('memory', 'redis')
            max_size (int): Maximum number of items in memory cache
            default_ttl (int): Default time-to-live in seconds
        """
        self._backend = backend
        self._max_size = max_size
        self._default_ttl = default_ttl
        
        # In-memory cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Optional Redis support
        self._redis_client = None
        if backend == 'redis':
            try:
                import redis.asyncio as redis
                self._redis_client = redis.Redis()
            except ImportError:
                raise ImportError("Redis backend requires 'redis' package. Install with: pip install redis")

    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (Optional[int]): Time-to-live in seconds
        
        Returns:
            bool: Whether cache operation was successful
        """
        try:
            serialized_value = json.dumps(value)
            expiry = ttl or self._default_ttl
            
            if self._backend == 'memory':
                # Manage cache size
                if len(self._cache) >= self._max_size:
                    # Remove oldest item
                    oldest_key = min(self._cache, key=lambda k: self._cache[k]['timestamp'])
                    del self._cache[oldest_key]
                
                self._cache[key] = {
                    'value': serialized_value,
                    'timestamp': datetime.now(),
                    'expiry': expiry
                }
                return True
            
            elif self._backend == 'redis' and self._redis_client:
                await self._redis_client.setex(key, expiry, serialized_value)
                return True
            
            return False
        
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def get(
        self, 
        key: str, 
        default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key (str): Cache key
            default (Optional[Any]): Default value if key not found
        
        Returns:
            Optional[Any]: Cached value or default
        """
        try:
            if self._backend == 'memory':
                cached_item = self._cache.get(key)
                
                if not cached_item:
                    return default
                
                # Check expiration
                if (datetime.now() - cached_item['timestamp']).total_seconds() > cached_item['expiry']:
                    del self._cache[key]
                    return default
                
                return json.loads(cached_item['value'])
            
            elif self._backend == 'redis' and self._redis_client:
                cached_value = await self._redis_client.get(key)
                return json.loads(cached_value) if cached_value else default
            
            return default
        
        except Exception as e:
            print(f"Cache get error: {e}")
            return default

    async def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key (str): Cache key to delete
        
        Returns:
            bool: Whether deletion was successful
        """
        try:
            if self._backend == 'memory':
                if key in self._cache:
                    del self._cache[key]
                return True
            
            elif self._backend == 'redis' and self._redis_client:
                await self._redis_client.delete(key)
                return True
            
            return False
        
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def clear(self) -> bool:
        """
        Clear the entire cache.
        
        Returns:
            bool: Whether cache clearing was successful
        """
        try:
            if self._backend == 'memory':
                self._cache.clear()
                return True
            
            elif self._backend == 'redis' and self._redis_client:
                await self._redis_client.flushdb()
                return True
            
            return False
        
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False



cache_manager = CacheManager()