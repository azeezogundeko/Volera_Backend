import asyncio
import functools
import inspect
from typing import TypeVar, Callable, Optional, Type, Union, Any
from utils.logging import logger

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
