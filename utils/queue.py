from asyncio import Queue, Semaphore
from api.auth.schema import UserIn
from .limiter import Limiter

# Architecture Configuration
RATE_LIMIT = "100/minute"  # Base rate limit
MAX_CONCURRENT = 100       # Simultaneous processing slots
QUEUE_SIZE = 200           # Max waiting requests
QUEUE_TIMEOUT = 30         # Seconds to wait in queue
PRIORITY_LEVELS = 3        # High, Medium, Low


limiter = Limiter()

# Global State
request_queues = [Queue(maxsize=QUEUE_SIZE) for _ in range(PRIORITY_LEVELS)]
processing_semaphore = Semaphore(MAX_CONCURRENT)
# limiter = Limiter()
# rate_limit = RateLimiter(times=100, minutes=1)


def determine_priority(user: UserIn, batch=False) -> int:
    """Business logic for request prioritization"""
    if "premium" in user.labels:
        return 0  # Highest priority

    if batch is True:
        return 2  # Lowest priority

    return 1  # Default priority