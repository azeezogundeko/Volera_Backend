from typing import List, Dict, Optional, Any
import asyncio
import httpx
from utils.logging import logger
from utils.decorator import async_retry, AsyncCache
from config import SEARXNG_BASE_URL, ApiKeyConfig, GOOGLE_SEARCH_ID

class MultiSearchTool:
    """A tool that combines multiple search engines with fallback behavior."""
    
    def __init__(self):
        self.searxng_base_url = SEARXNG_BASE_URL
        self.google_api_key = ApiKeyConfig.GOOGLE_SEARCH_API_KEY
        self.google_search_id = GOOGLE_SEARCH_ID
        self.duckduckgo_base_url = "https://api.duckduckgo.com"
        
    @async_retry(retries=3, delay=1.0)
    async def _searxng_search(
        self,
        query: str,
        num_results: int = 5,
        categories: Optional[str] = None,
        engines: Optional[str] = None,
        language: Optional[str] = None,
        time_range: Optional[str] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Perform a search using SearxNG."""
        try:
            params = {
                'q': query,
                'num': num_results,
                'categories': categories,
                'engines': engines,
                'language': language,
                'time_range': time_range,
                'format': 'json',
                **kwargs
            }
            params = {k: v for k, v in params.items() if v is not None}
            
            async with httpx.AsyncClient(timeout=10.0) as client:  # 10 second timeout
                response = await client.get(self.searxng_base_url + "/search", params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'error' in data:
                    logger.error(f"SearxNG API error: {data['error']}")
                    return []
                
                results = []
                for item in data.get('results', []):
                    result = {
                        'title': item.get('title', ''),
                        'link': item.get('url', ''),
                        'snippet': item.get('content', ''),
                        'source': item.get('engine', 'searxng')
                    }
                    results.append(result)
                return results
                
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            logger.error(f"Error in SearxNG search: {str(e)}")
            return []
    
    @AsyncCache(ttl=3600)
    @async_retry(retries=3, delay=1.0)
    async def _google_search(
        self,
        query: str,
        num_results: int = 5,
        search_type: Optional[str] = None,
        site: Optional[str] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Perform a search using Google Custom Search API."""
        try:
            if site and 'site:' not in query:
                if not site.startswith('site:'):
                    site = f"site:{site}"
                query = f"{site} {query}"
            
            params = {
                'key': self.google_api_key,
                'cx': self.google_search_id,
                'q': query,
                'num': min(num_results, 10)
            }
            
            # Only add searchType for image searches
            if search_type == 'image':
                params['searchType'] = search_type
            
            params.update(kwargs)
            params = {k: v for k, v in params.items() if v is not None}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if 'error' in data:
                    logger.error(f"Google Search API error: {data['error']}")
                    return []
                
                results = []
                for item in data.get('items', []):
                    result = {
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'google'
                    }
                    # Add image URL if available
                    if 'pagemap' in item and 'cse_image' in item['pagemap']:
                        result['image'] = item['pagemap']['cse_image'][0].get('src', '')
                    results.append(result)
                return results
                
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            logger.error(f"Error in Google search: {str(e)}")
            return []
    
    @async_retry(retries=3, delay=1.0)
    async def _duckduckgo_search(
        self,
        query: str,
        num_results: int = 5,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Perform a search using DuckDuckGo Instant Answer API."""
        try:
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'no_redirect': 1,
                't': 'volera'  # Custom source name
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.duckduckgo_base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                # Add the main result if available
                if data.get('AbstractText'):
                    results.append({
                        'title': data.get('Heading', ''),
                        'link': data.get('AbstractURL', ''),
                        'snippet': data.get('AbstractText', ''),
                        'source': 'duckduckgo'
                    })
                
                # Add related topics
                for topic in data.get('RelatedTopics', [])[:num_results-1]:
                    if 'Text' in topic and 'FirstURL' in topic:
                        results.append({
                            'title': topic.get('Text', '').split(' - ')[0],
                            'link': topic.get('FirstURL', ''),
                            'snippet': topic.get('Text', ''),
                            'source': 'duckduckgo'
                        })
                
                return results[:num_results]
                
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            logger.error(f"Error in DuckDuckGo search: {str(e)}")
            return []
    
    async def search(
        self,
        query: str,
        num_results: int = 5,
        search_type: Optional[str] = None,
        site: Optional[str] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform a search using multiple search engines with fallback behavior.
        First tries SearxNG, then Google if SearxNG fails, and finally DuckDuckGo.
        
        Args:
            query: The search query string
            num_results: Number of results to return
            search_type: Type of search (e.g., 'image' for image search)
            site: Optional domain to restrict search to
            **kwargs: Additional parameters to pass to the search engines
            
        Returns:
            List of search results with title, link, and snippet
        """
        # Try SearxNG first
        results = await self._searxng_search(query, num_results, **kwargs)
        if results:
            return results
            
        # If SearxNG fails, try Google
        results = await self._google_search(query, num_results, search_type, site, **kwargs)
        if results:
            return results
            
        # If both fail, try DuckDuckGo
        return await self._duckduckgo_search(query, num_results, **kwargs)
    
    async def search_images(
        self,
        query: str,
        num_results: int = 5,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform an image search using available engines.
        
        Args:
            query: The search query string
            num_results: Number of results to return
            **kwargs: Additional parameters to pass to the search engines
            
        Returns:
            List of image search results
        """
        # Try SearxNG image search first
        results = await self._searxng_search(
            query,
            num_results=num_results,
            categories="images",
            **kwargs
        )
        if results:
            return results
            
        # If SearxNG fails, try Google image search
        return await self._google_search(
            query,
            num_results=num_results,
            search_type='image',
            **kwargs
        )
    
    async def search_products(
        self,
        query: str,
        num_results: int = 5,
        site: Optional[str] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform a product search using available engines.
        
        Args:
            query: The search query string
            num_results: Number of results to return
            site: Optional domain to restrict search to
            **kwargs: Additional parameters to pass to the search engines
            
        Returns:
            List of product search results
        """
        # Try SearxNG product search first
        results = await self._searxng_search(
            query,
            num_results=num_results,
            **kwargs
        )
        if results:
            return results
            
        # If SearxNG fails, try Google search with product-specific terms
        if site:
            if not site.startswith('site:'):
                site = f"site:{site}"
            product_query = f"{site} {query}"

        return await self._google_search(
            product_query,
            num_results=num_results,
            **kwargs
        )

# Create a singleton instance
search_tool = MultiSearchTool() 