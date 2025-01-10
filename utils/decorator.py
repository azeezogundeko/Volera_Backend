import asyncio
import functools
import inspect
from typing import TypeVar, Callable, Optional, Type, Union, Any, Dict, Tuple
from utils.logging import logger
import time
from difflib import SequenceMatcher

T = TypeVar('T')

def async_retry(
    retries: int = 3,
    delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    A decorator for retrying async functions with exponential backoff.
    
    Args:
        retries (int): Maximum number of retries
        delay (float): Initial delay between retries in seconds
        max_delay (float): Maximum delay between retries in seconds
        exceptions (Exception | tuple[Exception]): Exception(s) to catch and retry on
        on_retry (Callable): Optional callback function called on each retry
        
    Example:
        @async_retry(retries=3, delay=1.0)
        async def my_function():
            pass
            
        @async_retry()
        @other_decorator
        async def decorated_function():
            pass
            
        class MyClass:
            @async_retry()
            async def my_method(self):
                pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Get the original function if it's already decorated
        original_func = getattr(func, '__wrapped__', func)
        
        # Check if the function is a coroutine
        is_coroutine = asyncio.iscoroutinefunction(original_func)
        if not is_coroutine:
            raise TypeError(f"Function {original_func.__name__} must be async")
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    if attempt == retries - 1:  # Last attempt
                        raise
                        
                    if on_retry:
                        on_retry(e, attempt + 1)
                    else:
                        logger.warning(
                            f"Retry {attempt + 1}/{retries} for {func.__name__} "
                            f"after error: {str(e)}"
                        )
                    
                    # Wait with exponential backoff
                    await asyncio.sleep(min(current_delay, max_delay))
                    current_delay *= 2
            
            # This should never happen due to the raise in the loop
            raise last_exception if last_exception else RuntimeError("Unexpected retry failure")
        
        # Preserve any existing attributes
        for attr_name, attr_value in inspect.getmembers(func):
            if not attr_name.startswith('__'):
                setattr(wrapper, attr_name, attr_value)
        
        return wrapper
    
    return decorator



def logging_(func):
    """
    A decorator to log the execution of functions and methods.
    Works with both synchronous and asynchronous functions.
    Catches and logs any errors.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error in async function {func.__qualname__}: {e}", exc_info=True)
                raise
    else:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error in function {func.__qualname__}: {e}", exc_info=True)
                raise
    return wrapper

def log_class(cls):
    """
    A class decorator to log all methods of a class.
    """
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        setattr(cls, name, logging_(method))
    return cls


class AsyncCache:
    """
    A decorator class that provides caching for async functions with TTL support 
    and similar query matching.
    """
    def __init__(self, ttl: int = 3600, similarity_threshold: float = 0.85):
        """
        Initialize the cache decorator.
        
        Args:
            ttl: Time to live in seconds for cached items (default: 1 hour)
            similarity_threshold: Threshold for considering queries similar (0.0 to 1.0)
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl
        self.similarity_threshold = similarity_threshold
        self._cleanup_task: Optional[asyncio.Task] = None

    def _is_similar(self, str1: str, str2: str) -> bool:
        """Check if two strings are similar enough."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() >= self.similarity_threshold

    def _find_similar_key(self, query: str) -> Optional[str]:
        """Find a similar query in the cache keys."""
        for cache_key in self.cache.keys():
            # Extract the query part from the cache key
            # Format is "function_name:args:kwargs"
            try:
                cached_query = eval(cache_key.split(':', 1)[1].split(':')[0])[0]
                if isinstance(cached_query, str) and self._is_similar(query, cached_query):
                    return cache_key
            except:
                continue
        return None

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator implementation that wraps the async function.
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Create a cache key from the function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Start the cleanup task if it's not running
            if not self._cleanup_task:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            current_time = time.time()
            
            # Check for exact match first
            if cache_key in self.cache:
                result, timestamp = self.cache[cache_key]
                if current_time - timestamp <= self.ttl:
                    return result
                del self.cache[cache_key]
            
            # If no exact match, check for similar queries
            # Only check for similarity if the first argument is a string (query)
            if args and isinstance(args[0], str):
                query = args[0]
                similar_key = self._find_similar_key(query)
                
                if similar_key and similar_key in self.cache:
                    result, timestamp = self.cache[similar_key]
                    if current_time - timestamp <= self.ttl:
                        logger.info(f"Using cached result for similar query: {query} ≈ {similar_key}")
                        return result
                    del self.cache[similar_key]
            
            # If no cache hit, call the original function
            result = await func(*args, **kwargs)
            self.cache[cache_key] = (result, current_time)
            return result
            
        return wrapper
    
    async def _periodic_cleanup(self) -> None:
        """
        Periodically clean up expired cache entries.
        """
        while True:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if current_time - timestamp > self.ttl
            ]
            
            for key in expired_keys:
                del self.cache[key]
                
            await asyncio.sleep(self.ttl / 2)
    
    def clear(self) -> None:
        """Clear the entire cache."""
        self.cache.clear()
    
    def get_cache_size(self) -> int:
        """Return the current number of cached items."""
        return len(self.cache)
    
    def remove(self, key: str) -> None:
        """Remove a specific key from the cache."""
        if key in self.cache:
            del self.cache[key]


# Example usage:
if __name__ == "__main__":
    # Example of how to use the cache decorator
    @AsyncCache(ttl=60, similarity_threshold=0.85)  # Cache results for 60 seconds
    async def fetch_data(query: str) -> Dict[str, Any]:
        # Simulate an API call
        await asyncio.sleep(1)
        return {"query": query, "timestamp": time.time()}

    async def test_cache():
        # First call - will execute the function
        result1 = await fetch_data("iphone 15 pro max")
        print("First call:", result1)
        
        # Similar query - should return cached result
        result2 = await fetch_data("iphone 15 pro")
        print("Similar query:", result2)
        
        # Very different query - will execute the function
        result3 = await fetch_data("macbook pro")
        print("Different query:", result3)
        
        # Similar to first query - should use cache
        result4 = await fetch_data("iphone15 pro max")
        print("Similar to first:", result4)
        
        # Wait for cache to expire
        await asyncio.sleep(61)
        
        # Should execute the function again
        result5 = await fetch_data("iphone 15 pro max")
        print("After expiry:", result5)

    asyncio.run(test_cache())
