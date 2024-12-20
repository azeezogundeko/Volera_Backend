import functools
import inspect
import hashlib
import json
from typing import Any, Callable, Optional

from .manager import cache_manager

def cached(
    key_prefix: Optional[str] = None, 
    ttl: Optional[int] = 3600,
    enabled: bool = True
):
    """
    Decorator to cache function results with flexible configuration.
    
    Args:
        key_prefix (Optional[str]): Custom prefix for cache key
        ttl (Optional[int]): Time-to-live for cached result in seconds
        enabled (bool): Whether caching is enabled
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # If caching is disabled, call the original function
            if not enabled:
                return await func(*args, **kwargs)
            
            def generate_cache_key():
                # Serialize arguments into a JSON string for consistent and robust key generation
                key_data = json.dumps({
                    "key_prefix": key_prefix or func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }, sort_keys=True, default=str)  # Use `default=str` to handle non-serializable objects
                return hashlib.md5(key_data.encode()).hexdigest()
            
            cache_key = generate_cache_key()
            
            # Try to retrieve from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # If not in cache, call the function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Additional utility decorators
def invalidate_cache(key_prefix: Optional[str] = None):
    """
    Decorator to invalidate cache entries related to a function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a cache key pattern to match
            def generate_cache_key_pattern():
                key_parts = [
                    key_prefix or func.__name__,
                    *[str(arg) for arg in args],
                    *[f"{k}={v}" for k, v in sorted(kwargs.items())]
                ]
                key_string = ":".join(key_parts)
                return hashlib.md5(key_string.encode()).hexdigest()
            
            # Call the original function first
            result = await func(*args, **kwargs)
            
            # Invalidate related cache entries
            # Note: This is a simplified approach. In a real-world scenario, 
            # you might want a more sophisticated cache invalidation strategy
            cache_key = generate_cache_key_pattern()
            await cache_manager.delete(cache_key)
            
            return result
        
        return wrapper
    return decorator