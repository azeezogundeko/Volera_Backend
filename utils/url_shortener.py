import redis
import secrets
import string
from typing import Optional
from diskcache import Cache
from config import PRODUCTION_MODE, URL_CACHE_DIR

PRODUCTION_MODE = "false"
class URLShortener:
    def __init__(self, redis_url="redis://redis:6379/0"):
        self.code_length = 6
        self.expiration = 7 * 24 * 60 * 60  # 7 days in seconds
        self.key_prefix = "url_short:"  # Namespace for URL shortener keys
        
        # Initialize the appropriate cache backend based on environment
        if PRODUCTION_MODE == "true":
            self.cache = redis.from_url(redis_url)
            self.is_redis = True
        else:
            self.cache = Cache(directory=str(URL_CACHE_DIR))
            self.is_redis = False

    def shorten_url(self, url: str) -> str:
        """
        Shortens a URL by generating a unique short code and storing it in the cache.
        
        Args:
            url (str): The original URL to shorten
            
        Returns:
            str: The generated short code
        """
        while True:
            short_code = self._generate_short_code()
            key = f"{self.key_prefix}{short_code}"
            
            if self.is_redis:
                # Use setnx for Redis to prevent race conditions
                if self.cache.setnx(key, url):
                    self.cache.expire(key, self.expiration)
                    return short_code
            else:
                # Use add() for diskcache to prevent race conditions
                if self.cache.add(key, url, expire=self.expiration):
                    return short_code

    def enlarge_url(self, short_code: str) -> Optional[str]:
        """
        Retrieves the original URL for a given short code.
        
        Args:
            short_code (str): The short code to look up
            
        Returns:
            str: Original URL if found and valid, None otherwise
        """
        key = f"{self.key_prefix}{short_code}"
        
        if self.is_redis:
            url = self.cache.get(key)
            return url.decode('utf-8') if url else None
        else:
            return self.cache.get(key, default=None)

    def _generate_short_code(self) -> str:
        """
        Generates a cryptographically secure random short code using base62 characters.
        
        Returns:
            str: Generated short code
        """
        alphabet = string.ascii_letters + string.digits  # Base62 characters
        return ''.join(secrets.choice(alphabet) for _ in range(self.code_length))

    def close(self):
        """
        Closes the cache connection. Should be called when done with the shortener.
        """
        if self.is_redis:
            self.cache.close()
        else:
            self.cache.close()

# Example usage
if __name__ == "__main__":
    shortener = URLShortener()
    
    try:
        # Shorten a URL
        short_code = shortener.shorten_url("https://www.example.com/very/long/url")
        print(f"Short code: {short_code}")
        
        # Enlarge a URL
        original_url = shortener.enlarge_url(short_code)
        print(f"Original URL: {original_url}")
    finally:
        shortener.close()