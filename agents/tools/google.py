import json
from typing import List, Optional, Dict, Any
import httpx
from utils.logging import logger
from utils.decorator import async_retry, AsyncCache
from config import ApiKeyConfig, GOOGLE_SEARCH_ID

class GoogleSearchTool:
    """A tool for performing Google Custom Search using their API"""
    
    def __init__(self):
        self.api_key = ApiKeyConfig.GOOGLE_SEARCH_API_KEY
        self.search_engine_id = GOOGLE_SEARCH_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    @AsyncCache(ttl=3600)  # Cache for 1 hour
    @async_retry(retries=3, delay=1.0)
    async def search(
        self,
        query: str,
        num_results: int = 5,
        search_type: Optional[str] = None,
        site: Optional[str] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google search using the Custom Search API.
        
        Args:
            query: The search query string
            num_results: Number of results to return (max 10)
            search_type: Type of search ('image' for image search)
            site: Optional domain to restrict search to (e.g. "amazon.com")
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            List of search results, each containing relevant information
        """
        try:
            # Handle site-specific search if provided
            if site:
                if not site.startswith('site:'):
                    site = f"site:{site}"
                query = f"{site} {query}"
            
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
            }
            
            # Only add num if it's a valid value
            print(num_results)
            if num_results and 1 <= num_results <= 10:
                params['num'] = num_results
            
            if search_type:
                params['searchType'] = search_type
                
            # Add any additional parameters from kwargs
            params.update(kwargs)
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                # print(data)
                
                if 'error' in data:
                    error_msg = data['error'].get('message', 'Unknown error in Google Search API')
                    logger.error(f"Google Search API error: {error_msg}")
                    return []
                
                # Extract and format results
                results = []
                for item in data.get('items', []):
                    result = {
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'google'
                    }
                    
                    # Add image-specific fields if present
                    if search_type == 'image':
                        image = item.get('image', {})
                        result.update({
                            'link': image.get('contextLink', ''),
                            'thumbnail': image.get('thumbnailLink', ''),
                            'image_url': item.get('link', ''),
                            'image_height': image.get('height', 0),
                            'image_width': image.get('width', 0)
                        })
                    
                    results.append(result)
                
                return results
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Google search: {str(e)}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Error performing Google search: {str(e)}", exc_info=True)
            return []
    
    @async_retry(retries=3, delay=1.0)
    async def search_images(
        self,
        query: str,
        num_results: int = 5,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google image search.
        
        Args:
            query: The search query string
            num_results: Number of results to return (max 10)
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            List of image search results
        """
        return await self.search(
            query,
            num_results=num_results,
            search_type='image',
            **kwargs
        )
    
    @async_retry(retries=2, delay=1.0)
    async def search_products(
        self,
        query: str,
        num_results: int = 5,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform a product-focused search by adding relevant terms.
        
        Args:
            query: The search query string
            num_results: Number of results to return (max 10)
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            List of product search results
        """
        results = await self.search(
            query,
            num_results=num_results,
            **kwargs
        )
        
        # Process results to extract product information
        processed_results = []
        for result in results:
            snippet = result.get('snippet', '').lower()
            price = None
            currency = None
            
            # Check for both $ and ₦ symbols
            if '$' in snippet or '₦' in snippet:
                try:
                    if '$' in snippet:
                        price_text = snippet[snippet.index('$'):].split()[0]
                        price = float(price_text.replace('$', '').replace(',', ''))
                        currency = 'USD'
                    elif '₦' in snippet:
                        price_text = snippet[snippet.index('₦'):].split()[0]
                        price = float(price_text.replace('₦', '').replace(',', ''))
                        currency = 'NGN'
                except (ValueError, IndexError):
                    pass
            
            processed_result = {
                **result,
                'price': price,
                'currency': currency,
                'type': 'product'
            }
            processed_results.append(processed_result)
        
        return processed_results

    @async_retry(retries=2, delay=1.0)
    async def search_shopping(
        self,
        query: str,
        num_results: int = 5,
        site: Optional[str] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google Shopping search using the Custom Search API.
        
        Args:
            query: The search query string
            num_results: Number of results to return (max 10)
            site: Optional domain to restrict search to (e.g. "amazon.com")
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            List of shopping results with product information
        """
        kwargs['tbm'] = 'shop'
        
        # Add site-specific search if domain provided
        if site:
            if not site.startswith('site:'):
                site = f"site:{site}"
            query = f"{site} {query}"
        
        results = await self.search(
            query,
            num_results=num_results,
            **kwargs
        )
        
        shopping_results = []
        for result in results:
            shopping_result = {
                **result,
                'type': 'shopping',
                'price': None,
                'currency': None,
                'merchant': None,
                'availability': None
            }
            
            snippet = result.get('snippet', '').lower()
            
            # Extract price and currency
            if '$' in snippet or '₦' in snippet:
                try:
                    if '$' in snippet:
                        price_text = snippet[snippet.index('$'):].split()[0]
                        shopping_result['price'] = float(price_text.replace('$', '').replace(',', ''))
                        shopping_result['currency'] = 'USD'
                    elif '₦' in snippet:
                        price_text = snippet[snippet.index('₦'):].split()[0]
                        shopping_result['price'] = float(price_text.replace('₦', '').replace(',', ''))
                        shopping_result['currency'] = 'NGN'
                except (ValueError, IndexError):
                    pass
            
            # Try to extract merchant name if present
            if ' from ' in snippet:
                try:
                    merchant = snippet.split(' from ')[1].split('.')[0].strip()
                    shopping_result['merchant'] = merchant
                except IndexError:
                    pass
            
            # Check availability
            availability_keywords = ['in stock', 'out of stock', 'available']
            for keyword in availability_keywords:
                if keyword in snippet:
                    shopping_result['availability'] = keyword
                    break
            
            shopping_results.append(shopping_result)
        
        return shopping_results


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_search():
        search_tool = GoogleSearchTool()
        
        # Test regular search
        results = await search_tool.search("Python programming")
        print("Regular search results:", json.dumps(results, indent=2))
        
        # Test image search
        image_results = await search_tool.search_images("cute cats")
        print("Image search results:", json.dumps(image_results, indent=2))
        
        # Test product search
        product_results = await search_tool.search_products("iPhone 15")
        print("Product search results:", json.dumps(product_results, indent=2))
        
        # Test shopping search
        shopping_results = await search_tool.search_shopping("MacBook Pro")
        print("Shopping search results:", json.dumps(shopping_results, indent=2))
    
    asyncio.run(test_search())

google_search = GoogleSearchTool()