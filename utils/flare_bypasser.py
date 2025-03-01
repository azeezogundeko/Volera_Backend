import httpx
import json
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin
import asyncio
from config import FLARE_BYPASSER_URL, PRODUCTION_MODE

class AsyncClient:
    """Async client for handling Cloudflare protection."""
    def __init__(self, base_url: str = FLARE_BYPASSER_URL, proxy: Optional[str] = None):
        if not PRODUCTION_MODE:
            self.client = None
            return
            
        self.base_url = base_url
        self.proxy = proxy
        self.client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            proxies=proxy if proxy else None
        )
        self._cookies = []
        self._user_agent = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def _get_solution(self, url: str) -> Dict[str, Any]:
        """Get Cloudflare solution for a URL."""
        if not self.client:
            return None
            
        endpoint = urljoin(self.base_url, "/v1")
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000
        }
        
        if self._cookies:
            payload["cookies"] = self._cookies
            
        response = await self.client.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if result["status"] == "ok":
            self._cookies = result["solution"]["cookies"]
            self._user_agent = result["solution"]["userAgent"]
            return result["solution"]
        return None
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make GET request with Cloudflare bypass."""
        if not self.client:
            return None
            
        solution = await self._get_solution(url)
        if not solution:
            raise Exception("Failed to get Cloudflare solution")
            
        headers = {
            "User-Agent": self._user_agent
        }
        
        cookies = {cookie["name"]: cookie["value"] for cookie in self._cookies}
        return await self.client.get(url, cookies=cookies, headers=headers, **kwargs)
    
    async def post(self, url: str, data: Dict = None, **kwargs) -> httpx.Response:
        """Make POST request with Cloudflare bypass."""
        if not self.client:
            return None
            
        solution = await self._get_solution(url)
        if not solution:
            raise Exception("Failed to get Cloudflare solution")
            
        headers = {
            "User-Agent": self._user_agent
        }
        
        cookies = {cookie["name"]: cookie["value"] for cookie in self._cookies}
        return await self.client.post(url, json=data, cookies=cookies, headers=headers, **kwargs)

class FlareBypasser:
    def __init__(self, base_url: str = FLARE_BYPASSER_URL):
        if not PRODUCTION_MODE:
            self.client = None
            return
            
        self.base_url = base_url or "http://flare-bypasser:20080"
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def get_cookies(self, url: str, max_timeout: int = 60000) -> Dict:
        """Get cookies after solving Cloudflare challenge."""
        if not self.client:
            return None
            
        endpoint = urljoin(self.base_url, "/v1")
        payload = {
            "cmd": "request.get_cookies",
            "url": url,
            "maxTimeout": max_timeout
        }
        
        response = await self.client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_page(self, url: str, max_timeout: int = 60000, cookies: Optional[List[Dict]] = None) -> Dict:
        """Get page content after solving Cloudflare challenge."""
        if not self.client:
            return None
            
        endpoint = urljoin(self.base_url, "/v1")
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": max_timeout
        }
        if cookies:
            payload["cookies"] = cookies
            
        response = await self.client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def make_post(self, url: str, post_data: Dict, max_timeout: int = 60000, cookies: Optional[List[Dict]] = None) -> Dict:
        """Make POST request after solving Cloudflare challenge."""
        if not self.client:
            return None
            
        endpoint = urljoin(self.base_url, "/v1")
        payload = {
            "cmd": "request.post",
            "url": url,
            "maxTimeout": max_timeout,
            "postData": post_data
        }
        if cookies:
            payload["cookies"] = cookies
            
        response = await self.client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()

# Global instances
flare_bypasser = FlareBypasser()
async_client = AsyncClient()

async def get_cloudflare_cookies(url: str) -> Dict:
    """Helper function to get Cloudflare cookies for a URL."""
    # Only process Jiji URLs in production mode
    if not PRODUCTION_MODE or not url.startswith("https://jiji."):
        return None
        
    try:
        result = await flare_bypasser.get_cookies(url)
        if result and result.get("status") == "ok":
            return {
                "cookies": result["solution"]["cookies"],
                "user_agent": result["solution"]["userAgent"]
            }
        return None
    except Exception as e:
        print(f"Error getting Cloudflare cookies: {str(e)}")
        return None

async def get_jiji_page(url: str, cookies: Optional[List[Dict]] = None) -> Optional[str]:
    """Helper function to get Jiji page content."""
    if not PRODUCTION_MODE or not url.startswith("https://jiji."):
        return None
        
    try:
        result = await flare_bypasser.get_page(url, cookies=cookies)
        if result and result.get("status") == "ok":
            return result["solution"]["response"]
        return None
    except Exception as e:
        print(f"Error getting Jiji page: {str(e)}")
        return None

async def get_page_with_client(url: str) -> Optional[str]:
    """Helper function to get page content using AsyncClient."""
    if not PRODUCTION_MODE:
        return None
        
    try:
        async with AsyncClient() as client:
            response = await client.get(url)
            return response.text
    except Exception as e:
        print(f"Error getting page with client: {str(e)}")
        return None

