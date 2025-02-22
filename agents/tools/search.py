from typing import List, Dict, Optional, Any
import asyncio
import httpx
import logging
import os
from utils.logging import logger
from utils.decorator import async_retry, AsyncCache
from config import SEARXNG_BASE_URL, ApiKeyConfig, GOOGLE_SEARCH_ID

logger = logging.getLogger(__name__)

class MultiSearchTool:
    """A tool that combines multiple search engines with fallback behavior."""
    
    def __init__(self):
        self.searxng_base_url = os.getenv('SEARXNG_BASE_URL', 'http://searxng:8080')
        self.google_api_key = os.getenv('GOOGLE_SERP_KEY')
        self.search_engine_id = os.getenv('SEARCH_ENGINE_ID')
        
        if not self.google_api_key or not self.search_engine_id:
            logger.warning("Google Search API credentials not configured")
        
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
        """Perform a search using SearxNG with result validation."""
        try:
            params = {
                'q': query,
                'num': num_results * 2,  # Request more results for filtering
                'categories': categories,
                'engines': engines,
                'language': language,
                'time_range': time_range,
                'format': 'json',
                **kwargs
            }
            params = {k: v for k, v in params.items() if v is not None}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.searxng_base_url + "/search", params=params)
                response.raise_for_status()
                data = response.json()

                print(data)
                
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

                # Validate results
                valid_results = self._validate_search_results(query, results)
                
                if not valid_results:
                    logger.warning("SearxNG results validation failed, falling back to Google")
                    return []

                print(valid_results)
                return valid_results[:num_results]
                
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            logger.error(f"Error in SearxNG search: {str(e)}")
            return []
    
    def _validate_search_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate search results for quality and relevance.
        Returns filtered results or empty list if validation fails.
        """
        if not results:
            return []

        # Convert query to lowercase for comparison
        query_terms = set(query.lower().split())
        
        valid_results = []
        for result in results:
            # Skip results with empty required fields
            if not result.get('title') or not result.get('link') or not result.get('snippet'):
                continue

            # Check for query term presence in title or snippet
            title_terms = set(result['title'].lower().split())
            snippet_terms = set(result['snippet'].lower().split())
            
            # Calculate relevance scores
            title_match = len(query_terms.intersection(title_terms)) / len(query_terms)
            snippet_match = len(query_terms.intersection(snippet_terms)) / len(query_terms)
            
            # Result must have good title or snippet match
            if title_match > 0.3 or snippet_match > 0.2:
                valid_results.append(result)

        # Ensure we have enough quality results
        if len(valid_results) < min(3, len(results) // 2):
            return []
            
        return valid_results
    
    # @AsyncCache(ttl=3600)
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
                'cx': self.search_engine_id,
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

                print(data)
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
        use_google_fallback: bool = True,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform a search using SearxNG with Google fallback.
        
        Args:
            query: The search query
            num_results: Number of results to return
            use_google_fallback: Whether to fall back to Google if SearxNG results are insufficient
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
        """
        # Try SearxNG first
        results = await self._searxng_search(query, num_results, **kwargs)
        
        # If SearxNG results are insufficient and fallback is enabled, try Google
        if not results and use_google_fallback:
            logger.info("Falling back to Google search")
            try:
                google_results = []
                async with httpx.AsyncClient(timeout=10.0) as client:
                    params = {
                        'key': self.google_api_key,
                        'cx': self.search_engine_id,
                        'q': query,
                        'num': num_results
                    }
                    response = await client.get(
                        'https://www.googleapis.com/customsearch/v1',
                        params=params
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    for item in data.get('items', []):
                        result = {
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'source': 'google'
                        }
                        google_results.append(result)
                    
                    return google_results[:num_results]
                    
            except Exception as e:
                logger.error(f"Error in Google fallback search: {str(e)}")
                return []
                
        return results
    
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
        product_query = query
        if site:
            if not site.startswith('site:'):
                site = f"site:{site}"
            product_query = f"{site} {query}"
            
        # Try SearxNG product search first
        results = await self._searxng_search(
            product_query,
            num_results=num_results,
            **kwargs
        )
        if results:
            return results
            
        # If SearxNG fails, try Google search with product-specific terms     
        return await self._google_search(
            product_query,
            num_results=num_results,
            **kwargs
        )

# Create a singleton instance
search_tool = MultiSearchTool() 