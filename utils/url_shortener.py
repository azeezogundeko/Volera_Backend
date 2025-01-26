import diskcache as dc
import secrets
import string
from typing import Optional

from config import URL_CACHE_DIR


class URLShortener:
    def __init__(self, cache_dir=URL_CACHE_DIR):
        self.cache = dc.Cache(cache_dir)
        self.code_length = 6
        self.expiration = 30 * 24 * 60 * 60  # 30 days in seconds

    def shorten_url(self, url):
        """
        Shortens a URL by generating a unique short code and storing it in the cache.
        
        Args:
            url (str): The original URL to shorten
            
        Returns:
            str: The generated short code
        """
        while True:
            short_code = self._generate_short_code()
            # Use add() instead of set() to prevent race conditions
            if self.cache.add(short_code, url, expire=self.expiration):
                return short_code

    def enlarge_url(self, short_code) -> Optional[str]:
        """
        Retrieves the original URL for a given short code.
        
        Args:
            short_code (str): The short code to look up
            
        Returns:
            str: Original URL if found and valid, None otherwise
        """
        return self.cache.get(short_code, default=None)

    def _generate_short_code(self):
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
        self.cache.close()

# Example usage
if __name__ == "__main__":
    shortener = URLShortener()
    
    # Shorten a URL
    short_code = shortener.shorten_url("https://www.example.com/very/long/url")
    print(f"Short code: {short_code}")
    
    # Enlarge a URL
    original_url = shortener.enlarge_url(short_code)
    print(f"Original URL: {original_url}")
    
    shortener.close()