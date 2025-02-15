# utils/limiter.py
from functools import wraps
from datetime import datetime
from typing import Dict, Optional
from fastapi import HTTPException, Request, status
from asyncio import Semaphore
import redis.asyncio as redis
from collections import defaultdict

class Limiter:
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the rate limiter.
        
        Args:
            redis_url: Optional Redis URL. If None, an in-memory store is used.
        """
        self.use_redis = redis_url is not None
        if self.use_redis:
            self.redis = redis.from_url(redis_url)
        else:
            self.memory_store = defaultdict(list)  # In-memory store for rate limits
        
        self._rate_limiters: Dict[str, "RateLimit"] = {}
        self.queue_semaphore = Semaphore(100)  # Max concurrent queue processors

    def limit(self, times: int = 100, minutes: int = 1, queue: bool = True, key_func=None):
        """
        Decorator to apply rate limiting to an endpoint.
        
        Args:
            times: Number of allowed requests per time window.
            minutes: Duration of the time window in minutes.
            queue: Whether to use the queue system for rate-limited requests.
            key_func: Optional function to generate the client identifier. 
                     If None, uses IP address.
        """
        def decorator(func):
            self._rate_limiters[func.__name__] = RateLimit(
                times=times,
                seconds=minutes * 60,
                queue=queue
            )
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                limit = self._rate_limiters[func.__name__]
                if key_func:
                    # Use custom key function if provided
                    client_id = await key_func(request, *args, **kwargs)
                else:
                    # Default to IP-based limiting
                    client_id = await self._get_client_id(request)
                
                if queue:
                    return await self._handle_with_queue(request, client_id, limit, func, args, kwargs)
                else:
                    return await self._handle_direct(request, client_id, limit, func, args, kwargs)
                
            return wrapper
        
        return decorator

    async def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier based on IP address."""
        return f"ip:{request.client.host}"  # Prefix to avoid collisions with other ID types

    async def _handle_with_queue(self, request: Request, client_id: str, 
                               limit: "RateLimit", func, args, kwargs):
        """Handle requests with queueing."""
        current = await self._check_limit(client_id, limit)
        
        if current["remaining"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {current['reset_in']} seconds"
            )
        
        async with self.queue_semaphore:
            return await func(request, *args, **kwargs)

    async def _handle_direct(self, request: Request, client_id: str,
                           limit: "RateLimit", func, args, kwargs):
        """Handle requests without queueing."""
        current = await self._check_limit(client_id, limit)
        
        if current["remaining"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {current['reset_in']} seconds"
            )
        
        return await func(request, *args, **kwargs)

    async def _check_limit(self, client_id: str, limit: "RateLimit") -> dict:
        """
        Check if the client has exceeded the rate limit.
        
        Args:
            client_id: Unique identifier for the client.
            limit: RateLimit object containing the limit configuration.
        
        Returns:
            Dictionary with remaining requests and reset time.
        """
        if self.use_redis:
            return await self._check_limit_redis(client_id, limit)
        else:
            return await self._check_limit_memory(client_id, limit)

    async def _check_limit_redis(self, client_id: str, limit: "RateLimit") -> dict:
        """Redis-based rate limiting using sorted sets."""
        key = f"rate_limit:{limit.name}:{client_id}"
        now = datetime.now().timestamp()
        window_start = now - limit.seconds

        async with self.redis.pipeline() as pipe:
            pipe.zremrangebyscore(key, 0, window_start)  # Remove old requests
            pipe.zcard(key)                              # Count current requests
            pipe.expire(key, limit.seconds)              # Set expiration
            results = await pipe.execute()

        current_count = results[1]
        if current_count >= limit.times:
            return {
                "remaining": 0,
                "reset_in": limit.seconds - (now - window_start)
            }

        async with self.redis.pipeline() as pipe:
            pipe.zadd(key, {now: now})
            pipe.expire(key, limit.seconds)
            await pipe.execute()

        return {
            "remaining": limit.times - current_count - 1,
            "reset_in": limit.seconds - (now - window_start)
        }

    async def _check_limit_memory(self, client_id: str, limit: "RateLimit") -> dict:
        """In-memory rate limiting using a sliding window."""
        now = datetime.now().timestamp()
        window_start = now - limit.seconds

        # Get the client's request timestamps
        timestamps = self.memory_store[client_id]
        
        # Remove old requests outside the time window
        timestamps = [ts for ts in timestamps if ts >= window_start]
        self.memory_store[client_id] = timestamps

        # Check if the limit is exceeded
        if len(timestamps) >= limit.times:
            return {
                "remaining": 0,
                "reset_in": limit.seconds - (now - window_start)
            }

        # Add the current request timestamp
        timestamps.append(now)
        self.memory_store[client_id] = timestamps

        return {
            "remaining": limit.times - len(timestamps),
            "reset_in": limit.seconds - (now - window_start)
        }

class RateLimit:
    """Configuration for a rate limit."""
    def __init__(self, times: int, seconds: int, queue: bool = True):
        self.times = times        # Allowed requests
        self.seconds = seconds    # Time window in seconds
        self.queue = queue        # Whether to use queue system
        self.name = f"limit_{times}_{seconds}"